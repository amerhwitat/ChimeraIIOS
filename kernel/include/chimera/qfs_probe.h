#pragma once
#include <stdint.h>
#include "chimera/block_device.h"

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_QFS_MAGIC 0x43484653u
#define CHIMERA_QFS_VERSION 1u
#define CHIMERA_QFS_MIN_BLOCK_SIZE 4096u
#define CHIMERA_QFS_MAX_BLOCK_SIZE 65536u
#define CHIMERA_QFS_PROBE_ABI 1u

typedef struct chimera_qfs_probe_info {
    uint32_t abi;
    uint32_t block_size;
    uint32_t sector_size;
    uint64_t total_blocks;
    uint64_t metadata_start;
    uint64_t data_start;
    uint64_t root_inode;
    uint8_t uuid[16];
} chimera_qfs_probe_info;

/* Validates the existing QFS v1 superblock against a registered block device.
 * This is format detection only; it does not mount directories or permit writes. */
int chimera_qfs_probe(uint32_t block_handle, chimera_qfs_probe_info *out);

static inline int chimera_qfs_valid_block_size(uint32_t size) {
    if (size < CHIMERA_QFS_MIN_BLOCK_SIZE || size > CHIMERA_QFS_MAX_BLOCK_SIZE)
        return 0;
    return (size & (size - 1u)) == 0;
}

#ifdef __cplusplus
}
#endif
