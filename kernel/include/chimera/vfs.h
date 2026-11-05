#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define KORONOS_VFS_ABI 1u
#define KORONOS_VFS_PATH_MAX 192u
#define KORONOS_VFS_FILE_MAX 32u
#define KORONOS_VFS_FILE_BYTES 4096u
#define KORONOS_VFS_O_RDONLY 0u
#define KORONOS_VFS_O_WRONLY 1u
#define KORONOS_VFS_O_RDWR 2u
#define KORONOS_VFS_O_CREAT 0x100u
#define KORONOS_VFS_O_TRUNC 0x200u
/* root_mounted is true only for a registered persistent/block-backed root mount. The current bootstrap store does not set it. */
typedef struct koronos_vfs_snapshot { uint32_t abi,initialized,root_mounted,tmp_mounted,files,open_handles; } koronos_vfs_snapshot;
/* Raw VFS handles are kernel-internal bootstrap handles. CPL3 code must use the process descriptor syscall layer. */
int koronos_vfs_init(void);
int koronos_vfs_mount_tmpfs(void);
int koronos_vfs_open(const char*,uint32_t);
int64_t koronos_vfs_read(int,void*,uint64_t);
int64_t koronos_vfs_write(int,const void*,uint64_t);
int64_t koronos_vfs_seek(int,int64_t,uint32_t);
int koronos_vfs_close(int);
int koronos_vfs_get_snapshot(koronos_vfs_snapshot*);
#ifdef __cplusplus
}
#endif
