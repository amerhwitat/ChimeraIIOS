#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define KORONOS_VFS_ABI 1u
#define KORONOS_VFS_MAX_FILES 512u
#define KORONOS_VFS_MAX_FDS 32u
int koronos_vfs_mount_cpio(const void *archive, uint64_t length);
int koronos_vfs_is_mounted(void);
uint32_t koronos_vfs_file_count(void);
int koronos_vfs_open(const char *path, uint32_t flags);
int64_t koronos_vfs_read(int fd, void *buffer, uint64_t length);
int64_t koronos_vfs_write(int fd, const void *buffer, uint64_t length);
int64_t koronos_vfs_seek(int fd, int64_t offset, uint32_t whence);
int koronos_vfs_close(int fd);
#ifdef __cplusplus
}
#endif
