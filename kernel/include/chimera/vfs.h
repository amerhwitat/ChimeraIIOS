#pragma once
#include <stdint.h>
#include "chimera/cpio_newc.h"

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_VFS_ABI 0x00010000u
#define CHIMERA_VFS_MAX_PATH CHIMERA_CPIO_NEWC_MAX_NAME

enum chimera_vfs_node_kind {
    CHIMERA_VFS_REGULAR = 1,
    CHIMERA_VFS_DIRECTORY = 2,
    CHIMERA_VFS_SYMLINK = 3
};

typedef struct chimera_vfs_node {
    const char *path;
    const void *data;
    uint64_t size;
    uint32_t mode;
    uint32_t uid;
    uint32_t gid;
    uint32_t parent_index;
    uint32_t kind;
} chimera_vfs_node;

typedef struct chimera_vfs_tree {
    uint32_t abi;
    uint32_t count;
    uint32_t capacity;
    uint32_t reserved;
    const void *archive;
    uint64_t archive_size;
    chimera_vfs_node *nodes;
} chimera_vfs_tree;

/*
 * Mount a raw CPIO newc archive into caller-owned staging storage. The root
 * pointer is published only after the complete archive, duplicate-path,
 * parent-directory and symlink checks succeed. The staging tree must not be
 * the currently published tree; keep its backing storage alive while mounted.
 * The archive is referenced in place and must also remain resident.
 */
int chimera_vfs_mount_newc(const void *archive, uint64_t archive_size,
                           chimera_vfs_tree *staging,
                           chimera_vfs_node *node_storage,
                           uint32_t node_capacity);
const chimera_vfs_tree *chimera_vfs_root(void);
const chimera_vfs_node *chimera_vfs_lookup(const char *absolute_or_relative_path);

#ifdef __cplusplus
}
#endif
