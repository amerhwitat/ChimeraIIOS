#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_VFS_ABI 1u
#define CHIMERA_VFS_MAX_MOUNTS 16u
#define CHIMERA_VFS_MAX_OPEN_FILES 128u
#define CHIMERA_VFS_MAX_PATH 255u

enum chimera_vfs_mount_flags { CHIMERA_VFS_MOUNT_RDONLY = 1u };
enum chimera_vfs_open_flags {
    CHIMERA_VFS_O_RDONLY = 0u,
    CHIMERA_VFS_O_WRONLY = 1u,
    CHIMERA_VFS_O_RDWR = 2u,
    CHIMERA_VFS_O_ACCMODE = 3u,
    CHIMERA_VFS_O_CREAT = 0x0100u,
    CHIMERA_VFS_O_EXCL = 0x0200u,
    CHIMERA_VFS_O_TRUNC = 0x0400u,
    CHIMERA_VFS_O_APPEND = 0x0800u
};
enum chimera_vfs_node_type { CHIMERA_VFS_REGULAR = 1u, CHIMERA_VFS_DIRECTORY = 2u, CHIMERA_VFS_DEVICE = 3u };

typedef struct chimera_vfs_stat {
    uint64_t size;
    uint32_t type;
    uint32_t mode;
} chimera_vfs_stat;

/* Backends receive canonical absolute paths relative to their mount root.
   All callbacks operate on kernel buffers; syscall adapters must validate and
   copy user memory before calling this interface. Missing mutation callbacks
   mean the backend is read-only for that operation. */
typedef struct chimera_vfs_ops {
    int (*lookup)(void *context, const char *path, chimera_vfs_stat *out);
    int (*read)(void *context, const char *path, uint64_t offset, void *buffer, uint64_t length, uint64_t *read_out);
    int (*write)(void *context, const char *path, uint64_t offset, const void *buffer, uint64_t length, uint64_t *written_out);
    int (*create)(void *context, const char *path, uint32_t type, uint32_t mode);
    int (*truncate)(void *context, const char *path, uint64_t size);
    int (*mkdir)(void *context, const char *path, uint32_t mode);
    int (*unlink)(void *context, const char *path, uint32_t directory);
    int (*rename)(void *context, const char *old_path, const char *new_path);
    int (*sync)(void *context);
} chimera_vfs_ops;

int chimera_vfs_init(void);
int chimera_vfs_mount(const char *mountpoint, const chimera_vfs_ops *ops, void *context, uint32_t flags);
int chimera_vfs_unmount(const char *mountpoint);
int64_t chimera_vfs_open(uint32_t pid, const char *path, uint32_t flags, uint32_t mode);
int64_t chimera_vfs_read(uint32_t pid, int64_t fd, void *buffer, uint64_t length);
int64_t chimera_vfs_write(uint32_t pid, int64_t fd, const void *buffer, uint64_t length);
int64_t chimera_vfs_seek(uint32_t pid, int64_t fd, int64_t offset, uint32_t whence);
int chimera_vfs_close(uint32_t pid, int64_t fd);
int chimera_vfs_close_process(uint32_t pid);
int chimera_vfs_stat_path(const char *path, chimera_vfs_stat *out);
int chimera_vfs_mkdir(const char *path, uint32_t mode);
int chimera_vfs_unlink(const char *path, uint32_t directory);
int chimera_vfs_rename(const char *old_path, const char *new_path);
int chimera_vfs_sync(void);
int chimera_vfs_normalize_path(const char *input, char output[CHIMERA_VFS_MAX_PATH + 1u]);

#ifdef __cplusplus
}
#endif
