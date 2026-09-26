#pragma once
#include <stdint.h>
#define CHIMERA_QFS_MAGIC 0x43484653u
#define CHIMERA_QFS_VERSION 1u
#define CHIMERA_QFS_DEFAULT_BLOCK_SIZE 4096u
#define CHIMERA_QFS_MIN_BLOCK_SIZE 4096u
#define CHIMERA_QFS_MAX_BLOCK_SIZE 65536u
struct chimera_qfs_superblock {
 uint32_t magic, version, block_size, sector_size;
 uint64_t total_blocks, metadata_start, data_start, root_inode;
 uint8_t uuid[16], reserved[400];
};
static inline int chimera_qfs_valid_block_size(uint32_t size) {
 if(size < CHIMERA_QFS_MIN_BLOCK_SIZE || size > CHIMERA_QFS_MAX_BLOCK_SIZE) return 0;
 return (size & (size - 1u)) == 0;
}
