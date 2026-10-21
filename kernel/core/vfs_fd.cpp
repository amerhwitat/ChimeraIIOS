#include "chimera/vfs_fd.h"

namespace {
static volatile uint32_t fd_table_lock=0;
struct FdGuard { FdGuard(){while(__sync_lock_test_and_set(&fd_table_lock,1u)){} } ~FdGuard(){__sync_lock_release(&fd_table_lock);} };
static chimera_vfs_fd *get(chimera_vfs_fd *table, uint32_t capacity, uint32_t pid, int fd) {
    if (!table || !pid || fd < 0 || static_cast<uint32_t>(fd) >= capacity ||
        capacity > CHIMERA_VFS_FD_MAX) return nullptr;
    chimera_vfs_fd *entry = &table[static_cast<uint32_t>(fd)];
    return entry->used && entry->owner_pid == pid ? entry : nullptr;
}
static int copy_path(char *dst, const char *src) {
    if (!dst || !src) return CHIMERA_VFS_EINVAL;
    uint32_t i = 0;
    while (src[i] && i + 1 < CHIMERA_VFS_PATH_MAX) {
        dst[i] = src[i];
        ++i;
    }
    if (src[i]) return CHIMERA_VFS_EINVAL;
    dst[i] = 0;
    return CHIMERA_VFS_OK;
}
}

extern "C" int chimera_vfs_fd_init(chimera_vfs_fd *table, uint32_t capacity) {
    FdGuard guard;
    if (!table || !capacity || capacity > CHIMERA_VFS_FD_MAX) return CHIMERA_VFS_EINVAL;
    for (uint32_t i = 0; i < capacity; ++i) table[i] = {};
    return CHIMERA_VFS_OK;
}

extern "C" int chimera_vfs_open(chimera_vfs_fd *table, uint32_t capacity, chimera_vfs *fs,
                                 uint32_t pid, uint32_t uid, uint32_t gid, const char *path,
                                 uint32_t flags) {
    FdGuard guard;
    const uint32_t valid = CHIMERA_FD_READ | CHIMERA_FD_WRITE | CHIMERA_FD_CREATE | CHIMERA_FD_TRUNC;
    if (!table || !fs || !pid || !path || !capacity || capacity > CHIMERA_VFS_FD_MAX ||
        !(flags & (CHIMERA_FD_READ | CHIMERA_FD_WRITE)) || (flags & ~valid) ||
        ((flags & CHIMERA_FD_TRUNC) && !(flags & CHIMERA_FD_WRITE)))
        return CHIMERA_VFS_EINVAL;

    uint32_t slot = capacity;
    for (uint32_t i = 0; i < capacity; ++i) {
        if (!table[i].used) { slot = i; break; }
    }
    if (slot == capacity) return CHIMERA_VFS_ENOSPC;

    int64_t read_probe = CHIMERA_VFS_ENOENT;
    int64_t write_probe = CHIMERA_VFS_ENOENT;
    if (flags & CHIMERA_FD_READ)
        read_probe = chimera_vfs_read(fs, path, 0, nullptr, 0, uid, gid);
    if (flags & CHIMERA_FD_WRITE)
        write_probe = chimera_vfs_write(fs, path, 0, nullptr, 0, uid, gid);

    const bool exists = read_probe >= 0 || write_probe >= 0;
    if (!exists) {
        // An access-denied probe means the path exists but this caller cannot
        // use it. Do not turn that into EEXIST by trying O_CREAT.
        if (read_probe == CHIMERA_VFS_EACCES || write_probe == CHIMERA_VFS_EACCES)
            return CHIMERA_VFS_EACCES;
        if (!(flags & CHIMERA_FD_CREATE)) {
            return CHIMERA_VFS_ENOENT;
        }
        const int rc = chimera_vfs_create(fs, path, 0644u, uid, gid);
        if (rc) return rc;
    } else {
        if ((flags & CHIMERA_FD_READ) && read_probe < 0) return static_cast<int>(read_probe);
        if ((flags & CHIMERA_FD_WRITE) && write_probe < 0) return static_cast<int>(write_probe);
    }

    if ((flags & CHIMERA_FD_TRUNC) && !(flags & CHIMERA_FD_WRITE)) return CHIMERA_VFS_EACCES;
    if (flags & CHIMERA_FD_TRUNC) {
        const int rc = chimera_vfs_truncate(fs, path, 0, uid, gid);
        if (rc) return rc;
    }

    chimera_vfs_fd entry{};
    entry.filesystem = fs;
    const int path_rc = copy_path(entry.path, path);
    if (path_rc) return path_rc;
    entry.owner_pid = pid;
    entry.uid = uid;
    entry.gid = gid;
    entry.flags = flags & ~(CHIMERA_FD_CREATE | CHIMERA_FD_TRUNC);
    entry.used = 1;
    table[slot] = entry;
    return static_cast<int>(slot);
}

extern "C" int64_t chimera_vfs_fd_read(chimera_vfs_fd *table, uint32_t capacity, uint32_t pid,
                                        int fd, void *buffer, uint64_t length) {
    FdGuard guard;
    chimera_vfs_fd *entry = get(table, capacity, pid, fd);
    if (!entry) return CHIMERA_VFS_EINVAL;
    if (!(entry->flags & CHIMERA_FD_READ)) return CHIMERA_VFS_EACCES;
    const int64_t count = chimera_vfs_read(entry->filesystem, entry->path, entry->offset,
                                            buffer, length, entry->uid, entry->gid);
    if (count > 0) entry->offset += static_cast<uint64_t>(count);
    return count;
}

extern "C" int64_t chimera_vfs_fd_write(chimera_vfs_fd *table, uint32_t capacity, uint32_t pid,
                                         int fd, const void *buffer, uint64_t length) {
    FdGuard guard;
    chimera_vfs_fd *entry = get(table, capacity, pid, fd);
    if (!entry) return CHIMERA_VFS_EINVAL;
    if (!(entry->flags & CHIMERA_FD_WRITE)) return CHIMERA_VFS_EACCES;
    const int64_t count = chimera_vfs_write(entry->filesystem, entry->path, entry->offset,
                                             buffer, length, entry->uid, entry->gid);
    if (count > 0) entry->offset += static_cast<uint64_t>(count);
    return count;
}

extern "C" int chimera_vfs_fd_seek(chimera_vfs_fd *table, uint32_t capacity, uint32_t pid,
                                    int fd, uint64_t offset) {
    FdGuard guard;
    chimera_vfs_fd *entry = get(table, capacity, pid, fd);
    if (!entry) return CHIMERA_VFS_EINVAL;
    entry->offset = offset;
    return CHIMERA_VFS_OK;
}

extern "C" int chimera_vfs_close(chimera_vfs_fd *table, uint32_t capacity, uint32_t pid, int fd) {
    FdGuard guard;
    chimera_vfs_fd *entry = get(table, capacity, pid, fd);
    if (!entry) return CHIMERA_VFS_EINVAL;
    *entry = {};
    return CHIMERA_VFS_OK;
}

extern "C" int chimera_vfs_close_process(chimera_vfs_fd *table, uint32_t capacity, uint32_t pid) {
    FdGuard guard;
    if (!table || !pid || !capacity || capacity > CHIMERA_VFS_FD_MAX) return CHIMERA_VFS_EINVAL;
    for (uint32_t i = 0; i < capacity; ++i) {
        if (table[i].used && table[i].owner_pid == pid) table[i] = {};
    }
    return CHIMERA_VFS_OK;
}
