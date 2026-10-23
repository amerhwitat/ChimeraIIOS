#include "chimera/block_device.h"
#include <stdint.h>

extern "C" int chimera_block_read(const chimera_block_device *d, uint64_t off,
                                    void *buf, uint64_t len) {
    if (!d || d->abi != CHIMERA_BLOCK_DEVICE_ABI || !d->read ||
        (!buf && len) || !d->logical_block_size || !d->capacity_bytes) return -22;
    if (d->present && !d->present(d->context)) return -19;
    if (off > d->capacity_bytes || len > d->capacity_bytes - off) return -5;
    if (len && off > UINT64_MAX - len) return -75;
    return len ? d->read(d->context, off, buf, len) : 0;
}
extern "C" int chimera_block_write(const chimera_block_device *d, uint64_t off,
                                     const void *buf, uint64_t len) {
    if (!d || d->abi != CHIMERA_BLOCK_DEVICE_ABI || !d->logical_block_size ||
        (!buf && len)) return -22;
    if (d->present && !d->present(d->context)) return -19;
    if (d->flags & CHIMERA_BLOCK_READ_ONLY) return -30;
    if (!d->write) return -38;
    if (off > d->capacity_bytes || len > d->capacity_bytes - off) return -5;
    if (len && off > UINT64_MAX - len) return -75;
    return len ? d->write(d->context, off, buf, len) : 0;
}
extern "C" int chimera_block_flush(const chimera_block_device *d) {
    if (!d || d->abi != CHIMERA_BLOCK_DEVICE_ABI) return -22;
    if (d->present && !d->present(d->context)) return -19;
    if (d->flags & CHIMERA_BLOCK_READ_ONLY) return 0;
    return d->flush ? d->flush(d->context) : -38;
}
