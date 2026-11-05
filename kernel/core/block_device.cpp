#include "chimera/block_device.h"

namespace {
struct Slot {
    chimera_block_ops ops;
    void *context;
    uint64_t sector_count;
    uint32_t sector_size;
    uint32_t flags;
    uint32_t generation;
    uint32_t active_io;
    char name[CHIMERA_BLOCK_NAME_MAX];
    bool used;
};
Slot slots[CHIMERA_BLOCK_MAX_DEVICES]{};
volatile uint32_t registry_lock = 0;

void lock_registry() { while (__sync_lock_test_and_set(&registry_lock, 1u)) {} }
void unlock_registry() { __sync_lock_release(&registry_lock); }

bool valid_name(const char *name, uint32_t *length) {
    if (!name || !length) return false;
    uint32_t n = 0;
    while (n < CHIMERA_BLOCK_NAME_MAX && name[n]) ++n;
    if (!n || n == CHIMERA_BLOCK_NAME_MAX) return false;
    *length = n;
    return true;
}

uint32_t make_handle(uint32_t index, uint32_t generation) {
    return (generation << 8) | (index + 1u);
}

Slot *lookup_locked(uint32_t handle, uint32_t *index_out) {
    const uint32_t low = handle & 0xffu;
    const uint32_t generation = handle >> 8;
    if (!low || low > CHIMERA_BLOCK_MAX_DEVICES || !generation) return nullptr;
    const uint32_t index = low - 1u;
    Slot &slot = slots[index];
    if (!slot.used || slot.generation != generation) return nullptr;
    if (index_out) *index_out = index;
    return &slot;
}

void release_io(uint32_t index) {
    lock_registry();
    if (index < CHIMERA_BLOCK_MAX_DEVICES && slots[index].active_io)
        --slots[index].active_io;
    unlock_registry();
}
}

extern "C" int chimera_block_register(const char *name, uint32_t sector_size,
                                       uint64_t sector_count, uint32_t flags,
                                       const chimera_block_ops *ops, void *context,
                                       uint32_t *out_handle) {
    uint32_t name_length = 0;
    if (!valid_name(name, &name_length) || !ops || !ops->read || !out_handle ||
        !sector_count || sector_size < 512u || sector_size > 65536u ||
        (sector_size & (sector_size - 1u)) ||
        (flags & ~CHIMERA_BLOCK_READ_ONLY) ||
        (!(flags & CHIMERA_BLOCK_READ_ONLY) && !ops->write))
        return CHM_BLOCK_EINVAL;

    lock_registry();
    for (uint32_t i = 0; i < CHIMERA_BLOCK_MAX_DEVICES; ++i) {
        Slot &slot = slots[i];
        if (slot.used) continue;
        if (!slot.generation) slot.generation = 1u;
        slot.ops = *ops;
        slot.context = context;
        slot.sector_count = sector_count;
        slot.sector_size = sector_size;
        slot.flags = flags;
        slot.active_io = 0;
        for (uint32_t j = 0; j < CHIMERA_BLOCK_NAME_MAX; ++j)
            slot.name[j] = j < name_length ? name[j] : 0;
        slot.used = true;
        *out_handle = make_handle(i, slot.generation);
        unlock_registry();
        return 0;
    }
    unlock_registry();
    return CHM_BLOCK_ENOSPC;
}

extern "C" int chimera_block_unregister(uint32_t handle) {
    lock_registry();
    uint32_t index = 0;
    Slot *slot = lookup_locked(handle, &index);
    if (!slot) { unlock_registry(); return CHM_BLOCK_ENODEV; }
    if (slot->active_io) { unlock_registry(); return CHM_BLOCK_EBUSY; }
    slot->used = false;
    slot->context = nullptr;
    slot->ops = {};
    slot->sector_count = 0;
    slot->sector_size = 0;
    slot->flags = 0;
    slot->name[0] = 0;
    slot->generation = (slot->generation + 1u) & 0x00ffffffu;
    if (!slot->generation) slot->generation = 1u;
    unlock_registry();
    (void)index;
    return 0;
}

extern "C" int chimera_block_get_info(uint32_t handle, chimera_block_info *out) {
    if (!out) return CHM_BLOCK_EINVAL;
    lock_registry();
    Slot *slot = lookup_locked(handle, nullptr);
    if (!slot) { unlock_registry(); return CHM_BLOCK_ENODEV; }
    out->abi = CHIMERA_BLOCK_ABI;
    out->handle = handle;
    out->sector_size = slot->sector_size;
    out->flags = slot->flags;
    out->sector_count = slot->sector_count;
    for (uint32_t i = 0; i < CHIMERA_BLOCK_NAME_MAX; ++i)
        out->name[i] = slot->name[i];
    unlock_registry();
    return 0;
}

extern "C" int chimera_block_read(uint32_t handle, uint64_t first_sector,
                                   uint32_t sector_count, void *buffer) {
    if (!sector_count || !buffer) return CHM_BLOCK_EINVAL;
    lock_registry();
    uint32_t index = 0;
    Slot *slot = lookup_locked(handle, &index);
    if (!slot) { unlock_registry(); return CHM_BLOCK_ENODEV; }
    if (first_sector >= slot->sector_count ||
        sector_count > slot->sector_count - first_sector) {
        unlock_registry(); return CHM_BLOCK_EINVAL;
    }
    ++slot->active_io;
    const chimera_block_ops ops = slot->ops;
    void *context = slot->context;
    unlock_registry();
    const int rc = ops.read(context, first_sector, sector_count, buffer);
    release_io(index);
    return rc == 0 ? 0 : CHM_BLOCK_EIO;
}

extern "C" int chimera_block_write(uint32_t handle, uint64_t first_sector,
                                    uint32_t sector_count, const void *buffer) {
    if (!sector_count || !buffer) return CHM_BLOCK_EINVAL;
    lock_registry();
    uint32_t index = 0;
    Slot *slot = lookup_locked(handle, &index);
    if (!slot) { unlock_registry(); return CHM_BLOCK_ENODEV; }
    if (slot->flags & CHIMERA_BLOCK_READ_ONLY) {
        unlock_registry(); return CHM_BLOCK_ENOTSUP;
    }
    if (first_sector >= slot->sector_count ||
        sector_count > slot->sector_count - first_sector) {
        unlock_registry(); return CHM_BLOCK_EINVAL;
    }
    ++slot->active_io;
    const chimera_block_ops ops = slot->ops;
    void *context = slot->context;
    unlock_registry();
    const int rc = ops.write(context, first_sector, sector_count, buffer);
    release_io(index);
    return rc == 0 ? 0 : CHM_BLOCK_EIO;
}

extern "C" int chimera_block_flush(uint32_t handle) {
    lock_registry();
    uint32_t index = 0;
    Slot *slot = lookup_locked(handle, &index);
    if (!slot) { unlock_registry(); return CHM_BLOCK_ENODEV; }
    if (!slot->ops.flush) { unlock_registry(); return CHM_BLOCK_ENOTSUP; }
    ++slot->active_io;
    const chimera_block_ops ops = slot->ops;
    void *context = slot->context;
    unlock_registry();
    const int rc = ops.flush(context);
    release_io(index);
    return rc == 0 ? 0 : CHM_BLOCK_EIO;
}
