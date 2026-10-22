#include "chimera/block.h"

/* Transport-neutral API only: hardware backends must supply real I/O callbacks. */

namespace {
struct Slot {
    bool used;
    chimera_block_device device;
};
static Slot g_slots[CHIMERA_BLOCK_MAX_DEVICES]{};
static volatile uint32_t g_lock = 0;

struct Guard {
    Guard() { while (__sync_lock_test_and_set(&g_lock, 1u)) {} }
    ~Guard() { __sync_lock_release(&g_lock); }
};

static int find_slot(uint32_t id) {
    for (uint32_t i = 0; i < CHIMERA_BLOCK_MAX_DEVICES; ++i)
        if (g_slots[i].used && g_slots[i].device.id == id) return static_cast<int>(i);
    return -1;
}

static bool valid_sector_size(uint32_t size) {
    return size >= CHIMERA_BLOCK_SECTOR_MIN &&
           size <= CHIMERA_BLOCK_SECTOR_MAX &&
           (size & (size - 1u)) == 0;
}

static int validate_io(const chimera_block_device *d, uint64_t lba,
                       uint32_t sectors, const void *buffer) {
    if (!d || !buffer || sectors == 0 ||
        sectors > CHIMERA_BLOCK_MAX_SECTORS_PER_IO) return CHIMERA_BLOCK_EINVAL;
    if (lba >= d->sector_count || static_cast<uint64_t>(sectors) > d->sector_count - lba)
        return CHIMERA_BLOCK_ERANGE;
    return CHIMERA_BLOCK_OK;
}
}

extern "C" int chimera_block_register(const chimera_block_device *device) {
    if (!device || !device->ops || !device->ops->read ||
        !device->ops->write || !valid_sector_size(device->sector_size) ||
        device->sector_count == 0) return CHIMERA_BLOCK_EINVAL;
    Guard guard;
    if (find_slot(device->id) >= 0) return CHIMERA_BLOCK_EINVAL;
    for (uint32_t i = 0; i < CHIMERA_BLOCK_MAX_DEVICES; ++i) {
        if (!g_slots[i].used) {
            g_slots[i].device = *device;
            g_slots[i].used = true;
            return CHIMERA_BLOCK_OK;
        }
    }
    return CHIMERA_BLOCK_ENOSPC;
}

extern "C" int chimera_block_read(uint32_t id, uint64_t lba, uint32_t sectors, void *buffer) {
    chimera_block_device d{};
    {
        Guard guard;
        const int slot = find_slot(id);
        if (slot < 0) return CHIMERA_BLOCK_ENODEV;
        d = g_slots[slot].device;
    }
    const int valid = validate_io(&d, lba, sectors, buffer);
    if (valid != CHIMERA_BLOCK_OK) return valid;
    return d.ops->read(d.context, lba, sectors, buffer) == 0
        ? CHIMERA_BLOCK_OK : CHIMERA_BLOCK_EIO;
}

extern "C" int chimera_block_write(uint32_t id, uint64_t lba, uint32_t sectors, const void *buffer) {
    chimera_block_device d{};
    {
        Guard guard;
        const int slot = find_slot(id);
        if (slot < 0) return CHIMERA_BLOCK_ENODEV;
        d = g_slots[slot].device;
    }
    const int valid = validate_io(&d, lba, sectors, buffer);
    if (valid != CHIMERA_BLOCK_OK) return valid;
    return d.ops->write(d.context, lba, sectors, buffer) == 0
        ? CHIMERA_BLOCK_OK : CHIMERA_BLOCK_EIO;
}

extern "C" int chimera_block_flush(uint32_t id) {
    chimera_block_device d{};
    {
        Guard guard;
        const int slot = find_slot(id);
        if (slot < 0) return CHIMERA_BLOCK_ENODEV;
        d = g_slots[slot].device;
    }
    if (!d.ops->flush) return CHIMERA_BLOCK_ENOTSUP;
    return d.ops->flush(d.context) == 0 ? CHIMERA_BLOCK_OK : CHIMERA_BLOCK_EIO;
}

extern "C" int chimera_block_unregister(uint32_t id) {
    Guard guard;
    const int slot = find_slot(id);
    if (slot < 0) return CHIMERA_BLOCK_ENODEV;
    g_slots[slot].used = false;
    g_slots[slot].device = {};
    return CHIMERA_BLOCK_OK;
}

extern "C" uint32_t chimera_block_device_count(void) {
    Guard guard;
    uint32_t count = 0;
    for (const Slot &slot : g_slots) if (slot.used) ++count;
    return count;
}
