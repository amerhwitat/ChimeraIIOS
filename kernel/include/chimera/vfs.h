#pragma once
#include <stdint.h>
#include "chimera/block.h"
#ifdef __cplusplus
extern "C" {
#endif

/* KoronosFS v2: a real block-backed filesystem.
 *
 * Layout inside a GPT partition (all offsets are 512-byte sectors):
 *   sector 0                 superblock
 *   sectors 1..8             inode table (64 x 64-byte inodes)
 *   sectors 9..16            data-block allocation bitmap
 *   sectors 17..N-1          file data blocks
 *
 * Files use 8 direct pointers, one single-indirect and one double-indirect
 * block. Every create/write/read/lookup is an actual block device operation;
 * fixed-marker "filesystems" are deliberately absent. */

#define KORONOSFS_V2_MAGIC "KORONOSFS2\x00\x00\x00\x00\x00"
#define KORONOSFS_V2_VERSION 2u
#define KORONOSFS_V2_SUPERBLOCK_SECTOR 0u
#define KORONOSFS_V2_INODE_TABLE_SECTOR 1u
#define KORONOSFS_V2_INODE_TABLE_SECTORS 8u
#define KORONOSFS_V2_INODE_COUNT 64u
#define KORONOSFS_V2_BITMAP_SECTOR 9u
#define KORONOSFS_V2_BITMAP_SECTORS 8u
#define KORONOSFS_V2_DATA_SECTOR 17u
#define KORONOSFS_V2_BLOCK_SIZE 512u
#define KORONOSFS_V2_NAME_MAX 56u
#define KORONOSFS_V2_CONTENT_MAX 262144u

typedef enum koronosfs_object_type {
    KORONOSFS_TYPE_DIRECTORY = 1u,
    KORONOSFS_TYPE_FILE = 2u
} koronosfs_object_type;

typedef enum koronosfs_state {
    KORONOSFS_STATE_CLEAN = 0u,
    KORONOSFS_STATE_DIRTY = 1u
} koronosfs_state;

typedef struct koronosfs_superblock {
    uint8_t magic[16];
    uint32_t version;
    uint32_t state;
    uint64_t sector_count;
    uint32_t inode_count;
    uint32_t inode_table_start;
    uint32_t inode_table_sectors;
    uint32_t bitmap_start;
    uint32_t bitmap_sectors;
    uint32_t data_start;
    uint32_t data_sectors;
    uint32_t root_inode;
    uint32_t generation;
    uint32_t mount_count;
    uint8_t reserved[436];
    uint32_t checksum;
} koronosfs_superblock_t;

typedef struct koronosfs_inode {
    uint8_t type;
    uint8_t flags;
    uint16_t reserved0;
    uint32_t size;
    uint32_t blocks;
    uint32_t direct[8];
    uint32_t indirect;
    uint32_t double_indirect;
    uint32_t generation;
    uint32_t checksum;
    uint8_t reserved1[4];
} koronosfs_inode_t;

typedef struct koronosfs_dirent {
    char name[KORONOSFS_V2_NAME_MAX];
    uint32_t inode;
    uint8_t type;
    uint8_t flags;
    uint8_t reserved[2];
} koronosfs_dirent_t;

#define KORONOS_VFS_FILE_MAGIC 0x4B465332u
#define KORONOS_VFS_MOUNT_MAX 4u

typedef struct koronos_vfs_file {
    uint32_t magic;
    int mount;
    uint32_t inode;
    uint32_t offset;
    uint32_t flags;
    uint64_t token;
} koronos_vfs_file_t;

int koronos_vfs_init(void);
int koronos_vfs_ready(void);

/* Formats the partition identified by its GPT type GUID. */
int koronos_vfs_format(uint32_t partition_index);
int koronos_vfs_find_by_type(const uint8_t type_guid[16], koronos_partition_t *out);
int koronos_vfs_mount(uint32_t partition_index, int *mount_out);
int koronos_vfs_unmount(int mount);
int koronos_vfs_sync(int mount);
int koronos_vfs_mount_state(void);
int koronos_vfs_verify(int mount);

int koronos_vfs_lookup(int mount, const char *name, uint32_t *inode_out);
int koronos_vfs_create(int mount, const char *name, uint32_t type, uint32_t *inode_out);
int koronos_vfs_unlink(int mount, const char *name);
int koronos_vfs_open(int mount, const char *name, koronos_vfs_file_t *file);
int koronos_vfs_close(koronos_vfs_file_t *file);
int koronos_vfs_read(koronos_vfs_file_t *file, uint8_t *buffer, uint32_t length, uint32_t *actual);
int koronos_vfs_write(koronos_vfs_file_t *file, const uint8_t *buffer, uint32_t length, uint32_t *actual);
int koronos_vfs_truncate(int mount, uint32_t inode);

/* Measured counters and digests for gates; no hardcoded pass values. */
uint64_t koronos_vfs_bytes_written(void);
uint64_t koronos_vfs_bytes_read(void);
uint64_t koronos_vfs_digest(const uint8_t *data, uint32_t length);
uint64_t koronos_vfs_file_digest(int mount, const char *name);
int koronos_vfs_superblock(int mount, koronosfs_superblock_t *out);
int koronos_vfs_inode(int mount, uint32_t inode, koronosfs_inode_t *out);

/* Whole-disk format helper shared by native-stack and installer phases. */
int koronos_vfs_format_disk(const uint8_t root_type_guid[16],
                            const uint8_t journal_type_guid[16],
                            koronos_partition_t *root_out,
                            koronos_partition_t *journal_out);

#ifdef __cplusplus
}
#endif
