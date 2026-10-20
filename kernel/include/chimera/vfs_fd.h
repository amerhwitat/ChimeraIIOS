#pragma once
#include <stdint.h>
#include "chimera/vfs.h"
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_VFS_FD_MAX 256u
enum { CHIMERA_FD_READ=1u, CHIMERA_FD_WRITE=2u, CHIMERA_FD_CREATE=4u, CHIMERA_FD_TRUNC=8u };
typedef struct chimera_vfs_fd {
    chimera_vfs *filesystem;
    char path[CHIMERA_VFS_PATH_MAX];
    uint64_t offset;
    uint32_t owner_pid, uid, gid, flags, used;
} chimera_vfs_fd;
int chimera_vfs_fd_init(chimera_vfs_fd *table, uint32_t capacity);
int chimera_vfs_open(chimera_vfs_fd *table, uint32_t capacity, chimera_vfs *fs,
                     uint32_t pid, uint32_t uid, uint32_t gid, const char *path, uint32_t flags);
int64_t chimera_vfs_fd_read(chimera_vfs_fd *table, uint32_t capacity, uint32_t pid, int fd, void *buffer, uint64_t length);
int64_t chimera_vfs_fd_write(chimera_vfs_fd *table, uint32_t capacity, uint32_t pid, int fd, const void *buffer, uint64_t length);
int chimera_vfs_fd_seek(chimera_vfs_fd *table, uint32_t capacity, uint32_t pid, int fd, uint64_t offset);
int chimera_vfs_close(chimera_vfs_fd *table, uint32_t capacity, uint32_t pid, int fd);
int chimera_vfs_close_process(chimera_vfs_fd *table, uint32_t capacity, uint32_t pid);
#ifdef __cplusplus
}
#endif
