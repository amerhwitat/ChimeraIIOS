#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_VFS_ABI 1u
#define CHIMERA_VFS_MAX_PROCESSES 64u
#define CHIMERA_VFS_FDS_PER_PROCESS 16u
#define CHIMERA_VFS_O_RDONLY 0u
/* The immutable archive memory must remain reserved for the lifetime of the mount.
 * Mount validates the complete newc stream and its exact target marker. */
int chimera_vfs_mount_readonly(const void *archive, uint64_t archive_size, const char *expected_target);
int chimera_vfs_is_mounted(void);
/* Explicit PID ownership is intentional until the syscall entry has a real current-task binding. */
int chimera_vfs_open_for(uint32_t pid, const char *path, uint32_t flags);
int chimera_vfs_read_for(uint32_t pid, int fd, void *buffer, uint64_t count, uint64_t *read_count);
int chimera_vfs_close_for(uint32_t pid, int fd);
#ifdef __cplusplus
}
#endif
