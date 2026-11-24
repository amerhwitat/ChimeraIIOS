#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

/* Partition-aware block layer backed by the native virtio-blk PCI device.
 *
 * All LBA values are 512-byte sectors. Partition discovery reads GPT (with a
 * protective MBR fallback); filesystems never assume fixed sector numbers. */

#define KORONOS_BLOCK_SECTOR_SIZE 512u
#define KORONOS_PARTITION_MAX 16u

typedef struct koronos_partition {
    uint8_t type_guid[16];
    uint8_t unique_guid[16];
    uint32_t index;
    uint64_t start_lba;
    uint64_t sector_count;
    uint64_t flags;
    char name[72];
} koronos_partition_t;

int koronos_block_init(void);
int koronos_block_ready(void);
uint64_t koronos_block_sector_count(void);
int koronos_block_read(uint64_t lba, uint8_t *buffer);
int koronos_block_write(uint64_t lba, const uint8_t *buffer);

int koronos_block_scan_partitions(void);
uint32_t koronos_block_partition_count(void);
int koronos_block_partition(uint32_t index, koronos_partition_t *out);
int koronos_block_find_partition(const uint8_t type_guid[16], koronos_partition_t *out);

/* Writes a protective MBR, GPT header and a two-partition entry array. The
 * caller passes explicit start/count values; nothing is inferred from old
 * fixed-sector markers. */
int koronos_block_format_gpt(uint64_t root_start, uint64_t root_sectors,
                             uint64_t journal_start, uint64_t journal_sectors,
                             const uint8_t root_type_guid[16],
                             const uint8_t journal_type_guid[16]);

/* Legacy exports retained for earlier callers and gates. */
uint32_t koronos_native_stack_block_sectors(void);
int koronos_native_block_init(void);
int koronos_native_block_read(uint32_t sector, uint8_t *buffer);
int koronos_native_block_write(uint32_t sector, const uint8_t *buffer);

#ifdef __cplusplus
}
#endif
