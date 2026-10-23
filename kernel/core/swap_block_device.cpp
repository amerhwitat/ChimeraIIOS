#include <stdint.h>
#include "chimera/block_device.h"
#include "chimera/swap.h"

namespace {
static chimera_block_device g_swap_device{};
static uint64_t g_extent_offset = 0;
static uint64_t g_extent_length = 0;
static bool g_extent_bound = false;

static bool extent_range(uint64_t offset, uint32_t length) {
    return g_extent_bound && offset <= g_extent_length &&
           static_cast<uint64_t>(length) <= g_extent_length - offset &&
           g_extent_offset <= UINT64_MAX - offset;
}
static int extent_read(void *, uint64_t offset, void *buffer, uint32_t length) {
    if (!buffer || length != KORONOS_SWAP_PAGE_SIZE || !extent_range(offset, length))
        return -1;
    return chimera_block_read(&g_swap_device, g_extent_offset + offset, buffer, length);
}
static int extent_write(void *, uint64_t offset, const void *buffer, uint32_t length) {
    if (!buffer || length != KORONOS_SWAP_PAGE_SIZE || !extent_range(offset, length))
        return -1;
    if (chimera_block_write(&g_swap_device, g_extent_offset + offset, buffer, length) != 0)
        return -1;
    // A successful swap store is not committed until the device reports its
    // write cache flushed. Unsupported flush is an I/O failure, not success.
    return chimera_block_flush(&g_swap_device) == 0 ? 0 : -1;
}
}

extern "C" int koronos_swap_init_block_extent(const chimera_block_device *device,
                                               uint64_t byte_offset, uint64_t length) {
    koronos_swap_snapshot snapshot{};
    if (koronos_swap_get_snapshot(&snapshot) != 0 || snapshot.initialized || g_extent_bound)
        return -1;
    if (!device || device->abi != CHIMERA_BLOCK_DEVICE_ABI ||
        !device->read || !device->write || !device->flush ||
        (device->flags & CHIMERA_BLOCK_READ_ONLY) || device->logical_block_size < 512u ||
        device->logical_block_size > KORONOS_SWAP_PAGE_SIZE ||
        (device->logical_block_size & (device->logical_block_size - 1u)) != 0u ||
        (KORONOS_SWAP_PAGE_SIZE % device->logical_block_size) != 0u ||
        !length || (byte_offset % device->logical_block_size) != 0u ||
        (length % KORONOS_SWAP_PAGE_SIZE) != 0u ||
        byte_offset > device->capacity_bytes ||
        length > device->capacity_bytes - byte_offset ||
        length < KORONOS_SWAP_PAGE_SIZE) return -2;
    if (device->present && !device->present(device->context)) return -3;

    // Do not publish the static callback context until all descriptor checks
    // pass. Swap is still disabled while the backend is being initialized.
    g_swap_device = *device;
    g_extent_offset = byte_offset;
    g_extent_length = length;
    g_extent_bound = true;
    const koronos_swap_backend backend{
        KORONOS_SWAP_ABI, KORONOS_SWAP_PAGE_SIZE, length,
        extent_read, extent_write, nullptr
    };
    if (koronos_swap_init(&backend) != 0) {
        g_extent_bound = false;
        g_extent_offset = g_extent_length = 0;
        g_swap_device = {};
        return -4;
    }
    return 0;
}
