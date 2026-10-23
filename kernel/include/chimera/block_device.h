#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_BLOCK_DEVICE_ABI 1u

enum chimera_block_device_flags {
    CHIMERA_BLOCK_READ_ONLY = 1u,
    CHIMERA_BLOCK_REMOVABLE = 2u
};

/* Driver callbacks use byte offsets, even when the underlying device is sector
   addressed. The adapter must perform overflow/capacity checks before I/O. */
typedef struct chimera_block_device {
    uint32_t abi;
    uint32_t logical_block_size;
    uint64_t capacity_bytes;
    uint32_t flags;
    void *context;
    int (*read)(void *context, uint64_t byte_offset, void *buffer, uint64_t length);
    int (*write)(void *context, uint64_t byte_offset, const void *buffer, uint64_t length);
    int (*flush)(void *context);
    int (*present)(void *context);
} chimera_block_device;

int chimera_block_read(const chimera_block_device *device, uint64_t offset,
                       void *buffer, uint64_t length);
int chimera_block_write(const chimera_block_device *device, uint64_t offset,
                        const void *buffer, uint64_t length);
int chimera_block_flush(const chimera_block_device *device);

#ifdef __cplusplus
}
#endif
