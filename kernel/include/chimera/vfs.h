#ifndef CHIMERA_VFS_H
#define CHIMERA_VFS_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_VFS_ABI 1u
#define CHIMERA_VFS_MAX_NODES 64u
#define CHIMERA_VFS_PATH_MAX 128u
#define CHIMERA_VFS_FILE_MAX 4096u

typedef enum chimera_vfs_type {
    CHIMERA_VFS_REGULAR = 1,
    CHIMERA_VFS_DIRECTORY = 2
} chimera_vfs_type;

typedef struct chimera_vfs_stat {
    uint32_t type;
    uint32_t size;
} chimera_vfs_stat;

/* Bounded in-memory VFS backend. This is not persistent storage and does not
 * claim FAT/ext2/ISO9660 support. Every path is absolute and traversal is
 * rejected. Mutations are serialized; file data and inode count are bounded. */
int chimera_vfs_init(void);
int chimera_vfs_mkdir(const char *path);
int chimera_vfs_create(const char *path);
int chimera_vfs_stat_path(const char *path, chimera_vfs_stat *out);
int64_t chimera_vfs_read(const char *path, uint64_t offset, void *buffer, uint64_t length);
int64_t chimera_vfs_write(const char *path, uint64_t offset, const void *buffer, uint64_t length);
int chimera_vfs_truncate(const char *path, uint64_t length);
int chimera_vfs_unlink(const char *path);
int chimera_vfs_rename(const char *old_path, const char *new_path);
uint32_t chimera_vfs_node_count(void);

#ifdef __cplusplus
}
#endif
#endif
