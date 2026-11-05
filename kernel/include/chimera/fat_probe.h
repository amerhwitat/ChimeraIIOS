#pragma once
#include <stdint.h>
#include "chimera/block_device.h"

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_FAT_PROBE_ABI 1u
enum chimera_fat_kind {
    CHM_FAT12 = 12,
    CHM_FAT16 = 16,
    CHM_FAT32 = 32,
    CHM_EXFAT = 64
};
typedef struct chimera_fat_probe_info {
    uint32_t abi;
    uint32_t kind;
    uint32_t sector_size;
    uint32_t sectors_per_cluster;
    uint64_t total_sectors;
    uint64_t fat_start_sector;
    uint64_t data_start_sector;
    uint64_t cluster_count;
    uint32_t root_cluster;
} chimera_fat_probe_info;

/* Read-only boot-sector/BPB validation. This does not mount or modify media. */
int chimera_fat_probe(uint32_t block_handle, chimera_fat_probe_info *out);

#ifdef __cplusplus
}
#endif
