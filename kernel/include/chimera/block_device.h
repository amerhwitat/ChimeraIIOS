#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_BLOCK_ABI 1u
#define CHIMERA_BLOCK_MAX_DEVICES 8u
#define CHIMERA_BLOCK_NAME_MAX 32u
#define CHIMERA_BLOCK_READ_ONLY 0x1u

enum chimera_block_error {
    CHM_BLOCK_EINVAL = -1,
    CHM_BLOCK_ENOSPC = -2,
    CHM_BLOCK_ENODEV = -3,
    CHM_BLOCK_EBUSY = -4,
    CHM_BLOCK_ENOTSUP = -5,
    CHM_BLOCK_EIO = -6
};

/* Callbacks operate in logical sectors. A callback returns zero on success. */
typedef struct chimera_block_ops {
    int (*read)(void *context, uint64_t first_sector,
                uint32_t sector_count, void *buffer);
    int (*write)(void *context, uint64_t first_sector,
                 uint32_t sector_count, const void *buffer);
    int (*flush)(void *context);
} chimera_block_ops;

typedef struct chimera_block_info {
    uint32_t abi;
    uint32_t handle;
    uint32_t sector_size;
    uint32_t flags;
    uint64_t sector_count;
    char name[CHIMERA_BLOCK_NAME_MAX];
} chimera_block_info;

/*
 * Register a block transport/backend. This is an interface and registry,
 * not a hardware driver: PCI/NVMe/AHCI/virtio transports must supply the
 * callbacks after their own device initialization and DMA validation.
 */
int chimera_block_register(const char *name, uint32_t sector_size,
                           uint64_t sector_count, uint32_t flags,
                           const chimera_block_ops *ops, void *context,
                           uint32_t *out_handle);
int chimera_block_unregister(uint32_t handle);
int chimera_block_get_info(uint32_t handle, chimera_block_info *out);
int chimera_block_read(uint32_t handle, uint64_t first_sector,
                       uint32_t sector_count, void *buffer);
int chimera_block_write(uint32_t handle, uint64_t first_sector,
                        uint32_t sector_count, const void *buffer);
int chimera_block_flush(uint32_t handle);

#ifdef __cplusplus
}
#endif
