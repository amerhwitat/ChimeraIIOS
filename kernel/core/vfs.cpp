#include "chimera/vfs.h"

namespace {
struct FsGuard { volatile uint32_t *lock; explicit FsGuard(chimera_vfs *fs):lock(fs?&fs->lock:nullptr){if(lock)while(__sync_lock_test_and_set(lock,1u)){} } ~FsGuard(){if(lock)__sync_lock_release(lock);} };
static bool add_overflow(uint64_t a, uint64_t b, uint64_t *out) {
    if (!out || b > UINT64_MAX - a) return true;
    *out = a + b;
    return false;
}

static int normalize(const char *in, char out[CHIMERA_VFS_PATH_MAX]) {
    if (!in || !out) return CHIMERA_VFS_EINVAL;
    while (*in == '/') ++in;
    uint32_t n = 0;
    if (!*in) return CHIMERA_VFS_EINVAL;
    while (*in) {
        if (*in == '\\') return CHIMERA_VFS_EINVAL;
        uint32_t seg = 0;
        while (in[seg] && in[seg] != '/') ++seg;
        if (!seg || (seg == 1 && in[0] == '.') ||
            (seg == 2 && in[0] == '.' && in[1] == '.')) return CHIMERA_VFS_EINVAL;
        if (n && n + 1 >= CHIMERA_VFS_PATH_MAX) return CHIMERA_VFS_EINVAL;
        if (n) out[n++] = '/';
        if (seg >= CHIMERA_VFS_PATH_MAX - n) return CHIMERA_VFS_EINVAL;
        for (uint32_t i = 0; i < seg; ++i) out[n++] = in[i];
        in += seg;
        if (*in == '/') {
            ++in;
            if (!*in) return CHIMERA_VFS_EINVAL;
        }
    }
    out[n] = 0;
    return CHIMERA_VFS_OK;
}

static bool equal(const char *a, const char *b) {
    uint32_t i = 0;
    while (a[i] && b[i] && a[i] == b[i]) ++i;
    return a[i] == b[i];
}

static chimera_vfs_node *find(chimera_vfs *fs, const char *path) {
    for (uint32_t i = 0; i < fs->node_capacity; ++i) {
        if (fs->nodes[i].used && equal(fs->nodes[i].path, path)) return &fs->nodes[i];
    }
    return nullptr;
}

static bool allowed(const chimera_vfs_node *node, uint32_t uid, uint32_t gid, uint32_t bit) {
    if (uid == 0) return true;
    const uint32_t shift = uid == node->uid ? 6u : (gid == node->gid ? 3u : 0u);
    return ((node->mode >> shift) & bit) != 0;
}

static int canonical(chimera_vfs *fs, const char *path, char out[CHIMERA_VFS_PATH_MAX]) {
    if (!fs || !fs->initialized) return CHIMERA_VFS_EINVAL;
    return normalize(path, out);
}
}

extern "C" int chimera_vfs_init(chimera_vfs *fs, chimera_vfs_node *nodes,
                                 uint32_t count, void *data, uint64_t data_size,
                                 uint64_t slot_size) {
    if (!fs || !nodes || !data || !count || count > CHIMERA_VFS_MAX_FILES ||
        !slot_size || data_size / slot_size < count) return CHIMERA_VFS_EINVAL;
    fs->nodes = nodes;
    fs->node_capacity = count;
    fs->data = static_cast<uint8_t *>(data);
    fs->data_capacity = data_size;
    fs->slot_size = slot_size;
    fs->initialized = 0;
    for (uint32_t i = 0; i < count; ++i) {
        nodes[i] = {};
        nodes[i].data_offset = static_cast<uint64_t>(i) * slot_size;
        nodes[i].capacity = slot_size;
    }
    fs->lock = 0;
    fs->initialized = 1;
    return CHIMERA_VFS_OK;
}

extern "C" int chimera_vfs_create(chimera_vfs *fs, const char *path,
                                   uint32_t mode, uint32_t uid, uint32_t gid) {
    FsGuard guard(fs);
    char key[CHIMERA_VFS_PATH_MAX];
    const int rc = canonical(fs, path, key);
    if (rc) return rc;
    if (find(fs, key)) return CHIMERA_VFS_EEXIST;
    for (uint32_t i = 0; i < fs->node_capacity; ++i) {
        chimera_vfs_node *node = &fs->nodes[i];
        if (node->used) continue;
        uint32_t j = 0;
        while (key[j] && j + 1 < CHIMERA_VFS_PATH_MAX) {
            node->path[j] = key[j];
            ++j;
        }
        node->path[j] = 0;
        node->uid = uid;
        node->gid = gid;
        node->mode = mode & 0777u;
        node->size = 0;
        node->used = 1;
        uint64_t end;
        if (add_overflow(node->data_offset, node->capacity, &end) || end > fs->data_capacity) {
            node->used = 0;
            node->path[0] = 0;
            return CHIMERA_VFS_ENOSPC;
        }
        for (uint64_t k = 0; k < node->capacity; ++k)
            fs->data[node->data_offset + k] = 0;
        return CHIMERA_VFS_OK;
    }
    return CHIMERA_VFS_ENOSPC;
}

extern "C" int chimera_vfs_stat_path(chimera_vfs *fs, const char *path,
                                      uint32_t uid, uint32_t gid, chimera_vfs_stat *out) {
    FsGuard guard(fs);
    if (!out) return CHIMERA_VFS_EINVAL;
    char key[CHIMERA_VFS_PATH_MAX];
    const int rc = canonical(fs, path, key);
    if (rc) return rc;
    chimera_vfs_node *node = find(fs, key);
    if (!node) return CHIMERA_VFS_ENOENT;
    if (!allowed(node, uid, gid, 4u)) return CHIMERA_VFS_EACCES;
    out->size = node->size;
    out->capacity = node->capacity;
    out->uid = node->uid;
    out->gid = node->gid;
    out->mode = node->mode;
    return CHIMERA_VFS_OK;
}

extern "C" int64_t chimera_vfs_read(chimera_vfs *fs, const char *path, uint64_t offset,
                                     void *buffer, uint64_t length, uint32_t uid, uint32_t gid) {
    FsGuard guard(fs);
    if (length && !buffer) return CHIMERA_VFS_EINVAL;
    char key[CHIMERA_VFS_PATH_MAX];
    const int rc = canonical(fs, path, key);
    if (rc) return rc;
    chimera_vfs_node *node = find(fs, key);
    if (!node) return CHIMERA_VFS_ENOENT;
    if (!allowed(node, uid, gid, 4u)) return CHIMERA_VFS_EACCES;
    if (offset >= node->size || !length) return 0;
    uint64_t count = node->size - offset;
    if (count > length) count = length;
    for (uint64_t i = 0; i < count; ++i)
        static_cast<uint8_t *>(buffer)[i] = fs->data[node->data_offset + offset + i];
    return static_cast<int64_t>(count);
}

extern "C" int64_t chimera_vfs_write(chimera_vfs *fs, const char *path, uint64_t offset,
                                      const void *buffer, uint64_t length, uint32_t uid, uint32_t gid) {
    FsGuard guard(fs);
    if (length && !buffer) return CHIMERA_VFS_EINVAL;
    char key[CHIMERA_VFS_PATH_MAX];
    const int rc = canonical(fs, path, key);
    if (rc) return rc;
    chimera_vfs_node *node = find(fs, key);
    if (!node) return CHIMERA_VFS_ENOENT;
    if (!allowed(node, uid, gid, 2u)) return CHIMERA_VFS_EACCES;
    uint64_t end;
    if (add_overflow(offset, length, &end) || end > node->capacity) return CHIMERA_VFS_EFBIG;
    if (offset > node->size) {
        for (uint64_t i = node->size; i < offset; ++i)
            fs->data[node->data_offset + i] = 0;
    }
    for (uint64_t i = 0; i < length; ++i)
        fs->data[node->data_offset + offset + i] = static_cast<const uint8_t *>(buffer)[i];
    if (end > node->size) node->size = end;
    return static_cast<int64_t>(length);
}

extern "C" int chimera_vfs_truncate(chimera_vfs *fs, const char *path, uint64_t size,
                                      uint32_t uid, uint32_t gid) {
    FsGuard guard(fs);
    char key[CHIMERA_VFS_PATH_MAX];
    const int rc = canonical(fs, path, key);
    if (rc) return rc;
    chimera_vfs_node *node = find(fs, key);
    if (!node) return CHIMERA_VFS_ENOENT;
    if (!allowed(node, uid, gid, 2u)) return CHIMERA_VFS_EACCES;
    if (size > node->capacity) return CHIMERA_VFS_EFBIG;
    const uint64_t old_size = node->size;
    const uint64_t begin = size < old_size ? size : old_size;
    const uint64_t end = size > old_size ? size : old_size;
    for (uint64_t i = begin; i < end; ++i) fs->data[node->data_offset + i] = 0;
    node->size = size;
    return CHIMERA_VFS_OK;
}

extern "C" int chimera_vfs_chmod(chimera_vfs *fs, const char *path, uint32_t mode,
                                   uint32_t caller_uid, uint32_t caller_gid) {
    FsGuard guard(fs);
    char key[CHIMERA_VFS_PATH_MAX];
    const int rc = canonical(fs, path, key);
    if (rc) return rc;
    chimera_vfs_node *node = find(fs, key);
    if (!node) return CHIMERA_VFS_ENOENT;
    if (caller_uid != 0 && caller_uid != node->uid) return CHIMERA_VFS_EACCES;
    (void)caller_gid;
    node->mode = mode & 0777u;
    return CHIMERA_VFS_OK;
}

extern "C" int chimera_vfs_chown(chimera_vfs *fs, const char *path, uint32_t owner_uid,
                                  uint32_t owner_gid, uint32_t caller_uid) {
    FsGuard guard(fs);
    char key[CHIMERA_VFS_PATH_MAX];
    const int rc = canonical(fs, path, key);
    if (rc) return rc;
    chimera_vfs_node *node = find(fs, key);
    if (!node) return CHIMERA_VFS_ENOENT;
    if (caller_uid != 0) return CHIMERA_VFS_EACCES;
    node->uid = owner_uid;
    node->gid = owner_gid;
    return CHIMERA_VFS_OK;
}

extern "C" int chimera_vfs_unlink(chimera_vfs *fs, const char *path,
                                   uint32_t caller_uid, uint32_t caller_gid) {
    FsGuard guard(fs);
    char key[CHIMERA_VFS_PATH_MAX];
    const int rc = canonical(fs, path, key);
    if (rc) return rc;
    chimera_vfs_node *node = find(fs, key);
    if (!node) return CHIMERA_VFS_ENOENT;
    if (caller_uid != 0 && caller_uid != node->uid) return CHIMERA_VFS_EACCES;
    (void)caller_gid;
    node->used = 0;
    node->path[0] = 0;
    node->size = 0;
    node->uid = node->gid = node->mode = 0;
    return CHIMERA_VFS_OK;
}
