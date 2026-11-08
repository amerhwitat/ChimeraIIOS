#include "chimera/vfs.h"

namespace {
constexpr uint32_t S_IFMT = 0170000u;
constexpr uint32_t S_IFREG = 0100000u;
constexpr uint32_t S_IFDIR = 0040000u;
constexpr uint32_t S_IFLNK = 0120000u;
const chimera_vfs_tree *published_root = nullptr;

static uint32_t node_kind(uint32_t mode) {
    switch (mode & S_IFMT) {
        case S_IFREG: return CHIMERA_VFS_REGULAR;
        case S_IFDIR: return CHIMERA_VFS_DIRECTORY;
        case S_IFLNK: return CHIMERA_VFS_SYMLINK;
        default: return 0;
    }
}
static uint32_t path_length(const char *path) {
    uint32_t n = 0;
    if (path) while (path[n]) ++n;
    return n;
}
static bool equal_n(const char *a, const char *b, uint32_t n) {
    for (uint32_t i = 0; i < n; ++i) if (a[i] != b[i]) return false;
    return true;
}
static int find_path(const chimera_vfs_tree *tree, const char *path, uint32_t length) {
    for (uint32_t i = 0; i < tree->count; ++i) {
        const char *candidate = tree->nodes[i].path;
        if (candidate && path_length(candidate) == length &&
            equal_n(candidate, path, length)) return static_cast<int>(i);
    }
    return -1;
}
static bool safe_symlink(const void *raw, uint32_t size, uint32_t parent_depth) {
    if (!raw || size == 0 || size > CHIMERA_VFS_MAX_PATH) return false;
    const auto *target = static_cast<const uint8_t *>(raw);
    if (target[0] == '/') return false;
    uint32_t depth = parent_depth;
    uint32_t component = 0;
    for (uint32_t i = 0; i <= size; ++i) {
        if (i < size && target[i] == 0) return false;
        if (i != size && target[i] != '/') continue;
        const uint32_t length = i - component;
        if (length == 0) return false;
        if (length == 1 && target[component] == '.') {
            // A current-directory component is harmless.
        } else if (length == 2 && target[component] == '.' && target[component + 1] == '.') {
            if (depth == 0) return false;
            --depth;
        } else {
            ++depth;
        }
        component = i + 1;
    }
    return true;
}
struct BuildContext { chimera_vfs_tree *tree; bool root_seen; };
static int append_entry(void *opaque, const char *path, uint32_t mode,
                        uint32_t uid, uint32_t gid, const void *data,
                        uint32_t size) {
    auto *ctx = static_cast<BuildContext *>(opaque);
    chimera_vfs_tree *tree = ctx->tree;
    const uint32_t length = path_length(path);
    const uint32_t kind = node_kind(mode);
    if (!kind) return -1;
    if (length == 0) {
        if (kind != CHIMERA_VFS_DIRECTORY || size != 0 || ctx->root_seen) return -1;
        ctx->root_seen = true;
        tree->nodes[0].mode = mode;
        tree->nodes[0].uid = uid;
        tree->nodes[0].gid = gid;
        return 0;
    }
    if (tree->count >= tree->capacity || find_path(tree, path, length) >= 0)
        return -1;
    if (kind == CHIMERA_VFS_DIRECTORY && size != 0) return -1;
    chimera_vfs_node &node = tree->nodes[tree->count++];
    node.path = path;
    node.data = data;
    node.size = size;
    node.mode = mode;
    node.uid = uid;
    node.gid = gid;
    node.parent_index = 0xFFFFFFFFu;
    node.kind = kind;
    return 0;
}
static int validate_tree(chimera_vfs_tree *tree) {
    for (uint32_t i = 1; i < tree->count; ++i) {
        chimera_vfs_node &node = tree->nodes[i];
        const uint32_t length = path_length(node.path);
        uint32_t slash = length;
        while (slash && node.path[slash - 1] != '/') --slash;
        const uint32_t parent_length = slash ? slash - 1u : 0u;
        const char *parent_path = slash ? node.path : "";
        const int parent = find_path(tree, parent_path, parent_length);
        if (parent < 0 || tree->nodes[parent].kind != CHIMERA_VFS_DIRECTORY)
            return -2;
        node.parent_index = static_cast<uint32_t>(parent);
        if (node.kind == CHIMERA_VFS_SYMLINK) {
            uint32_t depth = 0;
            for (uint32_t p = 0; p < parent_length; ++p)
                if (node.path[p] == '/') ++depth;
            if (parent_length) ++depth;
            if (!safe_symlink(node.data, static_cast<uint32_t>(node.size), depth))
                return -3;
        }
    }
    return 0;
}
}

extern "C" int chimera_vfs_mount_newc(const void *archive, uint64_t archive_size,
                                       chimera_vfs_tree *staging,
                                       chimera_vfs_node *node_storage,
                                       uint32_t node_capacity) {
    if (!archive || !staging || !node_storage || node_capacity < 1u ||
        staging == published_root || archive_size == 0) return -1;
    staging->abi = CHIMERA_VFS_ABI;
    staging->count = 1u;
    staging->capacity = node_capacity;
    staging->reserved = 0u;
    staging->archive = archive;
    staging->archive_size = archive_size;
    staging->nodes = node_storage;
    staging->nodes[0] = {"", nullptr, 0u, 0040755u, 0u, 0u, 0u, CHIMERA_VFS_DIRECTORY};

    BuildContext context{staging, false};
    const chimera_cpio_newc_ops ops{append_entry};
    chimera_cpio_newc_summary summary{};
    const int walked = chimera_cpio_newc_walk(archive, archive_size, &ops, &context, &summary);
    if (walked != 0) return -10 + walked;
    const int validated = validate_tree(staging);
    if (validated != 0) return validated;
    __atomic_store_n(&published_root, staging, __ATOMIC_RELEASE);
    return 0;
}

extern "C" const chimera_vfs_tree *chimera_vfs_root(void) {
    return __atomic_load_n(&published_root, __ATOMIC_ACQUIRE);
}

extern "C" const chimera_vfs_node *chimera_vfs_lookup(const char *path) {
    const chimera_vfs_tree *root = chimera_vfs_root();
    if (!root || !path) return nullptr;
    while (*path == '/') ++path;
    const uint32_t length = path_length(path);
    const int found = find_path(root, path, length);
    return found < 0 ? nullptr : &root->nodes[found];
}
