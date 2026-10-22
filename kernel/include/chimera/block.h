#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_BLOCK_MAX_DEVICES 16u
#define CHIMERA_BLOCK_MAX_SECTORS_PER_IO 128u
#define CHIMERA_BLOCK_SECTOR_MIN 512u
#define CHIMERA_BLOCK_SECTOR_MAX 4096u

enum chimera_block_status {
    CHIMERA_BLOCK_OK = 0,
    CHIMERA_BLOCK_EINVAL = -1,
    CHIMERA_BLOCK_ENOSPC = -2,
    CHIMERA_BLOCK_ENODEV = -3,
    CHIMERA_BLOCK_EIO = -4,
    CHIMERA_BLOCK_ERANGE = -5,
    CHIMERA_BLOCK_ENOTSUP = -6
};

struct chimera_block_ops {
    int (*read)(void *context, uint64_t lba, uint32_t sectors, void *buffer);
    int (*write)(void *context, uint64_t lba, uint32_t sectors, const void *buffer);
    int (*flush)(void *context);
};

struct chimera_block_device {
    uint32_t id;
    uint32_t sector_size;
    uint64_t sector_count;
    const struct chimera_block_ops *ops;
    void *context;
};

int chimera_block_register(const struct chimera_block_device *device);
int chimera_block_read(uint32_t device_id, uint64_t lba, uint32_t sectors, void *buffer);
int chimera_block_write(uint32_t device_id, uint64_t lba, uint32_t sectors, const void *buffer);
int chimera_block_flush(uint32_t device_id);
int chimera_block_unregister(uint32_t device_id);
uint32_t chimera_block_device_count(void);

#ifdef __cplusplus
}
#endif
