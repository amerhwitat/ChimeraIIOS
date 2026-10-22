#include "chimera/virtio_blk.h"

namespace {
constexpr uint8_t STATUS_ACKNOWLEDGE = 1u;
constexpr uint8_t STATUS_DRIVER = 2u;
constexpr uint8_t STATUS_DRIVER_OK = 4u;
constexpr uint8_t STATUS_FEATURES_OK = 8u;
constexpr uint8_t STATUS_FAILED = 128u;
constexpr uint32_t VIRTIO_F_VERSION_1 = 32u;
constexpr uint32_t VIRTIO_BLK_F_FLUSH = 9u;
constexpr uint32_t VIRTIO_BLK_T_IN = 0u;
constexpr uint32_t VIRTIO_BLK_T_OUT = 1u;
constexpr uint32_t VIRTIO_BLK_T_FLUSH = 4u;
constexpr uint16_t DESC_NEXT = 1u;
constexpr uint16_t DESC_WRITE = 2u;
constexpr uint8_t VIRTIO_BLK_S_OK = 0u;
constexpr uint32_t SECTOR_SIZE = 512u;
constexpr uint32_t MAX_SECTORS = KORONOS_VIRTIO_BLK_QUEUE_MAX;

struct __attribute__((packed)) Descriptor {
    uint64_t address;
    uint32_t length;
    uint16_t flags;
    uint16_t next;
};
struct __attribute__((packed)) UsedElement { uint32_t id; uint32_t length; };
struct __attribute__((packed)) RequestHeader { uint32_t type; uint32_t reserved; uint64_t sector; };

static uint16_t *avail_flags(koronos_virtio_blk *d) {
    return reinterpret_cast<uint16_t *>(d->ring.virtual_address + 2048u);
}
static volatile uint16_t *avail_idx(koronos_virtio_blk *d) {
    return reinterpret_cast<volatile uint16_t *>(d->ring.virtual_address + 2050u);
}
static uint16_t *avail_ring(koronos_virtio_blk *d) {
    return reinterpret_cast<uint16_t *>(d->ring.virtual_address + 2052u);
}
static volatile uint16_t *used_idx(koronos_virtio_blk *d) {
    return reinterpret_cast<volatile uint16_t *>(d->ring.virtual_address + 2308u + 2u);
}
static volatile UsedElement *used_ring(koronos_virtio_blk *d) {
    return reinterpret_cast<volatile UsedElement *>(d->ring.virtual_address + 2312u);
}
static Descriptor *descriptors(koronos_virtio_blk *d) {
    return reinterpret_cast<Descriptor *>(d->ring.virtual_address);
}
static RequestHeader *request_header(koronos_virtio_blk *d) {
    return reinterpret_cast<RequestHeader *>(d->request.virtual_address);
}
static uint8_t *request_status(koronos_virtio_blk *d) {
    return reinterpret_cast<uint8_t *>(d->request.virtual_address + sizeof(RequestHeader));
}
static uint64_t read_le64(const volatile uint8_t *p) {
    uint64_t value = 0;
    for (unsigned i = 0; i < 8; ++i) value |= static_cast<uint64_t>(p[i]) << (i * 8u);
    return value;
}
static void barrier() { __asm__ volatile("mfence" ::: "memory"); }
static void relax(koronos_virtio_blk *d) {
    if (d->transport.relax) d->transport.relax(d->transport.context);
    else __asm__ volatile("pause");
}
static bool wait_status(koronos_virtio_blk *d, uint8_t mask, uint8_t expected) {
    for (uint32_t i = 0; i < KORONOS_VIRTIO_BLK_WAIT_LIMIT; ++i) {
        if ((d->transport.common->device_status & mask) == expected) return true;
        relax(d);
    }
    return false;
}
static int issue(koronos_virtio_blk *d, uint32_t type, uint64_t lba,
                 uint32_t sectors, void *buffer, bool device_writes) {
    if (!d || !d->attached || d->busy) return -1;
    if (sectors > MAX_SECTORS || (type != VIRTIO_BLK_T_FLUSH && (!sectors || !buffer)))
        return -1;
    d->busy = 1;
    const size_t bytes = static_cast<size_t>(sectors) * SECTOR_SIZE;
    if (type == VIRTIO_BLK_T_OUT)
        for (size_t i = 0; i < bytes; ++i)
            reinterpret_cast<uint8_t *>(d->data.virtual_address)[i] =
                static_cast<const uint8_t *>(buffer)[i];

    RequestHeader *h = request_header(d);
    h->type = type; h->reserved = 0; h->sector = lba;
    *request_status(d) = 0xffu;
    Descriptor *desc = descriptors(d);
    desc[0] = {d->request.physical_address, sizeof(RequestHeader), DESC_NEXT, 1};
    if (type == VIRTIO_BLK_T_FLUSH) {
        desc[1] = {d->request.physical_address + sizeof(RequestHeader), 1, DESC_WRITE, 0};
        desc[0].next = 1;
    } else {
        desc[1] = {d->data.physical_address, static_cast<uint32_t>(bytes),
                   static_cast<uint16_t>(DESC_NEXT | (device_writes ? DESC_WRITE : 0)), 2};
        desc[2] = {d->request.physical_address + sizeof(RequestHeader), 1, DESC_WRITE, 0};
    }
    uint16_t avail = *avail_idx(d);
    avail_ring(d)[avail % d->queue_size] = 0;
    barrier();
    *avail_idx(d) = static_cast<uint16_t>(avail + 1u);
    barrier();

    const uint16_t old_used = d->last_used;
    const uint16_t notify_off = d->transport.common->queue_notify_off;
    const uint64_t byte_off = static_cast<uint64_t>(notify_off) * d->transport.notify_multiplier;
    if (byte_off + sizeof(uint16_t) > d->transport.notify_length) {
        d->busy = 0;
        return -1;
    }
    volatile uint16_t *notify = reinterpret_cast<volatile uint16_t *>(
        const_cast<uint8_t *>(d->transport.notify_base) + byte_off);
    *notify = 0;
    barrier();
    bool complete = false;
    for (uint32_t i = 0; i < KORONOS_VIRTIO_BLK_WAIT_LIMIT; ++i) {
        barrier();
        if (*used_idx(d) != old_used) { complete = true; break; }
        relax(d);
    }
    if (!complete) {
        d->busy = 0;
        return -2; // bounded timeout; queue/device recovery is required before reuse
    }
    volatile UsedElement *used = used_ring(d);
    volatile UsedElement elem = used[old_used % d->queue_size];
    d->last_used = static_cast<uint16_t>(old_used + 1u);
    if (elem.id != 0 || *request_status(d) != VIRTIO_BLK_S_OK) {
        d->busy = 0;
        return -3;
    }
    barrier();
    if (type == VIRTIO_BLK_T_IN)
        for (size_t i = 0; i < bytes; ++i)
            static_cast<uint8_t *>(buffer)[i] =
                reinterpret_cast<const uint8_t *>(d->data.virtual_address)[i];
    d->busy = 0;
    return 0;
}
static int block_read(void *ctx, uint64_t lba, uint32_t count, void *buffer) {
    koronos_virtio_blk *d = static_cast<koronos_virtio_blk *>(ctx);
    return issue(d, VIRTIO_BLK_T_IN, lba, count, buffer, true);
}
static int block_write(void *ctx, uint64_t lba, uint32_t count, const void *buffer) {
    return issue(static_cast<koronos_virtio_blk *>(ctx), VIRTIO_BLK_T_OUT,
                 lba, count, const_cast<void *>(buffer), false);
}
static int block_flush(void *ctx) {
    return issue(static_cast<koronos_virtio_blk *>(ctx), VIRTIO_BLK_T_FLUSH, 0, 0, nullptr, false);
}
static const chimera_block_ops block_ops{block_read, block_write, block_flush};

static void release(koronos_virtio_blk *d) {
    if (d->transport.common) d->transport.common->device_status = 0;
    if (d->data.physical_address) (void)koronos_dma_free(&d->data);
    if (d->request.physical_address) (void)koronos_dma_free(&d->request);
    if (d->ring.physical_address) (void)koronos_dma_free(&d->ring);
    d->attached = 0;
    d->busy = 0;
}
}

extern "C" int koronos_virtio_blk_attach(koronos_virtio_blk *d,
                                          const koronos_virtio_blk_transport *t,
                                          uint32_t block_id) {
    if (!d || !t || !t->common || !t->notify_base || !t->device_config ||
        t->device_config_length < 8 || !t->notify_length ||
        t->notify_multiplier == 0 || t->dma_mask < 0xffffffffull) return -1;
    *d = {};
    d->transport = *t;
    d->id = block_id;
    volatile koronos_virtio_pci_common_cfg *c = t->common;
    c->device_status = 0;
    barrier();
    c->device_status = STATUS_ACKNOWLEDGE;
    c->device_status |= STATUS_DRIVER;

    c->device_feature_select = 1;
    barrier();
    const uint32_t feature_hi = c->device_feature;
    if ((feature_hi & (1u << (VIRTIO_F_VERSION_1 - 32u))) == 0) {
        c->device_status |= STATUS_FAILED;
        return -2;
    }
    c->driver_feature_select = 1;
    c->driver_feature = 1u; // VIRTIO_F_VERSION_1
    c->device_feature_select = 0;
    barrier();
    const uint32_t feature_lo = c->device_feature;
    c->driver_feature_select = 0;
    c->driver_feature = (feature_lo & (1u << VIRTIO_BLK_F_FLUSH)) |
                        (1u << VIRTIO_BLK_F_FLUSH & feature_lo);
    c->device_status |= STATUS_FEATURES_OK;
    barrier();
    if (!(c->device_status & STATUS_FEATURES_OK)) {
        c->device_status |= STATUS_FAILED;
        return -3;
    }

    c->queue_select = 0;
    barrier();
    const uint16_t offered = c->queue_size;
    if (!offered) { c->device_status |= STATUS_FAILED; return -4; }
    uint16_t q = 1;
    while (q <= KORONOS_VIRTIO_BLK_QUEUE_MAX / 2u && q * 2u <= offered) q *= 2u;
    d->queue_size = q;
    if (koronos_dma_alloc(4096, 4096, t->dma_mask, &d->ring) != 0 ||
        koronos_dma_alloc(4096, 4096, t->dma_mask, &d->request) != 0 ||
        koronos_dma_alloc(MAX_SECTORS * SECTOR_SIZE, 4096, t->dma_mask, &d->data) != 0) {
        release(d); c->device_status |= STATUS_FAILED; return -5;
    }
    c->queue_size = q;
    c->queue_desc = d->ring.physical_address;
    c->queue_driver = d->ring.physical_address + 2048u;
    c->queue_device = d->ring.physical_address + 2308u;
    c->queue_enable = 1;
    barrier();
    if (!wait_status(d, STATUS_FAILED, 0)) { release(d); return -6; }
    d->last_used = 0;
    d->free_head = 0;
    d->attached = 1;

    const uint64_t capacity = read_le64(t->device_config);
    if (!capacity) { release(d); return -7; }
    d->block = {block_id, SECTOR_SIZE, capacity, &block_ops, d};
    if (chimera_block_register(&d->block) != CHIMERA_BLOCK_OK) {
        release(d); return -8;
    }
    c->device_status |= STATUS_DRIVER_OK;
    barrier();
    if (!(c->device_status & STATUS_DRIVER_OK)) {
        (void)chimera_block_unregister(block_id); release(d); return -9;
    }
    return 0;
}

extern "C" void koronos_virtio_blk_detach(koronos_virtio_blk *d) {
    if (!d) return;
    if (d->attached) (void)chimera_block_unregister(d->id);
    release(d);
}
