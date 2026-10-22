#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_RAMFS_ABI 1u
#define CHIMERA_RAMFS_MAX_ENTRIES 4096u
#define CHIMERA_RAMFS_MAX_PATH 255u
#define CHIMERA_RAMFS_MAX_FILE_BYTES (64ull * 1024ull * 1024ull)
#define CHIMERA_RAMFS_MAX_TOTAL_BYTES (64ull * 1024ull * 1024ull)
typedef void *(*chimera_ramfs_alloc_fn)(uint64_t size, void *context);
typedef void (*chimera_ramfs_free_fn)(void *ptr, void *context);
typedef struct chimera_ramfs_allocator { chimera_ramfs_alloc_fn alloc; chimera_ramfs_free_fn free; void *context; } chimera_ramfs_allocator;
typedef struct chimera_ramfs_limits { uint32_t max_entries; uint32_t max_path_bytes; uint64_t max_file_bytes; uint64_t max_total_bytes; } chimera_ramfs_limits;
typedef struct chimera_ramfs_node chimera_ramfs_node;
typedef enum chimera_ramfs_status { CHIMERA_RAMFS_OK=0, CHIMERA_RAMFS_E_ARGUMENT=-1, CHIMERA_RAMFS_E_LIMIT=-2, CHIMERA_RAMFS_E_HEADER=-3, CHIMERA_RAMFS_E_BOUNDS=-4, CHIMERA_RAMFS_E_PATH=-5, CHIMERA_RAMFS_E_TYPE=-6, CHIMERA_RAMFS_E_CHECKSUM=-7, CHIMERA_RAMFS_E_TRAILER=-8, CHIMERA_RAMFS_E_NOMEM=-9, CHIMERA_RAMFS_E_DUPLICATE=-10, CHIMERA_RAMFS_E_CONFLICT=-11 } chimera_ramfs_status;
/* Builds an unpublished staging tree. Failure releases every allocation and leaves *root_out NULL. Publish only after success while holding the rootfs/VFS lock. Only regular files/directories are accepted. */
int chimera_ramfs_extract_newc(const void *archive, uint64_t archive_size, const chimera_ramfs_allocator *allocator, const chimera_ramfs_limits *limits, chimera_ramfs_node **root_out);
void chimera_ramfs_destroy(chimera_ramfs_node *root, const chimera_ramfs_allocator *allocator);
const chimera_ramfs_node *chimera_ramfs_lookup(const chimera_ramfs_node *root, const char *absolute_or_relative_path);
int chimera_ramfs_read(const chimera_ramfs_node *node, uint64_t offset, void *destination, uint64_t length, uint64_t *read_out);
uint64_t chimera_ramfs_file_size(const chimera_ramfs_node *node);
int chimera_ramfs_is_directory(const chimera_ramfs_node *node);
#ifdef __cplusplus
}
#endif
