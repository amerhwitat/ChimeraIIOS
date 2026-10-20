#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_VFS_ABI 1u
#define CHIMERA_VFS_PATH_MAX 128u
#define CHIMERA_VFS_MAX_FILES 64u
enum { CHIMERA_VFS_OK=0, CHIMERA_VFS_EINVAL=-1, CHIMERA_VFS_ENOENT=-2,
       CHIMERA_VFS_EEXIST=-3, CHIMERA_VFS_ENOSPC=-4, CHIMERA_VFS_EACCES=-5,
       CHIMERA_VFS_EFBIG=-6 };
typedef struct chimera_vfs_node {
    char path[CHIMERA_VFS_PATH_MAX];
    uint32_t uid, gid, mode;
    uint64_t data_offset, size, capacity;
    uint32_t used;
} chimera_vfs_node;
/* Bounded volatile RAM VFS. Caller owns metadata and data buffers. Each file
 * gets a fixed-size slot; no allocator, disk persistence, or implicit growth. */
typedef struct chimera_vfs {
    chimera_vfs_node *nodes;
    uint32_t node_capacity;
    uint8_t *data;
    uint64_t data_capacity, slot_size;
    uint32_t initialized;
} chimera_vfs;
typedef struct chimera_vfs_stat { uint64_t size, capacity; uint32_t uid, gid, mode; } chimera_vfs_stat;
int chimera_vfs_init(chimera_vfs*, chimera_vfs_node*, uint32_t, void*, uint64_t, uint64_t);
int chimera_vfs_create(chimera_vfs*, const char*, uint32_t, uint32_t, uint32_t);
int chimera_vfs_stat_path(chimera_vfs*, const char*, uint32_t, uint32_t, chimera_vfs_stat*);
int64_t chimera_vfs_read(chimera_vfs*, const char*, uint64_t, void*, uint64_t, uint32_t, uint32_t);
int64_t chimera_vfs_write(chimera_vfs*, const char*, uint64_t, const void*, uint64_t, uint32_t, uint32_t);
int chimera_vfs_truncate(chimera_vfs*, const char*, uint64_t, uint32_t, uint32_t);
int chimera_vfs_chmod(chimera_vfs*, const char*, uint32_t, uint32_t, uint32_t);
int chimera_vfs_chown(chimera_vfs*, const char*, uint32_t, uint32_t, uint32_t);
int chimera_vfs_unlink(chimera_vfs*, const char*, uint32_t, uint32_t);
#ifdef __cplusplus
}
#endif
