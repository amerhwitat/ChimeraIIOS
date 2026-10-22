#include "chimera/virtio_pci.h"

namespace {
static uint16_t le16(const uint8_t *p) {
    return static_cast<uint16_t>(p[0]) | (static_cast<uint16_t>(p[1]) << 8u);
}
static uint32_t le32(const uint8_t *p) {
    return static_cast<uint32_t>(p[0]) |
           (static_cast<uint32_t>(p[1]) << 8u) |
           (static_cast<uint32_t>(p[2]) << 16u) |
           (static_cast<uint32_t>(p[3]) << 24u);
}
static bool add_region(koronos_virtio_pci_region *region, uint8_t bar,
                       uint32_t offset, uint32_t length) {
    if (!region || region->present || bar >= 6u || length == 0u ||
        offset > UINT32_MAX - length) return false;
    region->bar = bar;
    region->offset = offset;
    region->length = length;
    region->present = 1;
    return true;
}
}

extern "C" int koronos_virtio_pci_parse_caps(
    const uint8_t config[KORONOS_VIRTIO_PCI_CONFIG_SPACE_SIZE],
    koronos_virtio_pci_caps *out) {
    if (!config || !out) return -1;
    *out = {};
    const uint16_t vendor = le16(config);
    const uint16_t device = le16(config + 2);
    if (vendor != 0x1af4u || (device != 0x1042u && device != 0x1001u)) return -2;

    /* PCI Status bit 4 indicates that a capability list is present. */
    if ((le16(config + 6) & (1u << 4u)) == 0) return -3;
    uint8_t ptr = config[0x34];
    if ((ptr & 3u) != 0) return -4;
    uint8_t visited[256] = {};
    uint8_t covered[256] = {};
    unsigned count = 0;
    while (ptr) {
        if (ptr < 0x40u || ptr > 0xfcu || (ptr & 3u) != 0 ||
            visited[ptr] || covered[ptr] || ++count > 48u) return -4;
        visited[ptr] = 1;
        const uint8_t id = config[ptr];
        const uint8_t next = config[ptr + 1u];
        if ((next & 3u) != 0) return -4;
        if (id == KORONOS_VIRTIO_PCI_CAP_VENDOR_ID) {
            const uint8_t cap_len = config[ptr + 2u];
            const uint8_t type = config[ptr + 3u];
            if (cap_len < 16u || static_cast<unsigned>(ptr) + cap_len > 256u)
                return -5;
            for (unsigned i = ptr; i < static_cast<unsigned>(ptr) + cap_len; ++i) {
                if (covered[i] && i != ptr) return -5;
                covered[i] = 1;
            }
            const uint8_t bar = config[ptr + 4u];
            const uint32_t offset = le32(config + ptr + 8u);
            const uint32_t length = le32(config + ptr + 12u);
            koronos_virtio_pci_region *region = nullptr;
            switch (type) {
                case 1: region = &out->common; break;
                case 2:
                    region = &out->notify;
                    if (cap_len < 20u) return -6;
                    out->notify_multiplier = le32(config + ptr + 16u);
                    out->has_notify_multiplier = 1;
                    break;
                case 3: region = &out->isr; break;
                case 4: region = &out->device; break;
                default: break; /* Ignore other well-formed Virtio capabilities. */
            }
            if (region && !add_region(region, bar, offset, length)) return -7;
            if (type == 2 && out->notify_multiplier == 0u) return -8;
        }
        ptr = next;
    }
    if (!out->common.present || !out->notify.present ||
        !out->device.present || !out->has_notify_multiplier) return -9;
    if (out->common.length < 56u || out->notify.length < 2u ||
        out->device.length < 8u) return -10;

    /* A BAR offset/length pair is untrusted device metadata. Reject overlapping
     * Virtio windows in the same BAR rather than allowing one mapping to alias
     * another register region. The ranges were overflow-checked in add_region.
     */
    const koronos_virtio_pci_region *regions[] = {
        &out->common, &out->notify, &out->isr, &out->device
    };
    for (unsigned i = 0; i < sizeof(regions) / sizeof(regions[0]); ++i) {
        if (!regions[i]->present) continue;
        const uint64_t begin_i = regions[i]->offset;
        const uint64_t end_i = begin_i + regions[i]->length;
        for (unsigned j = i + 1; j < sizeof(regions) / sizeof(regions[0]); ++j) {
            if (!regions[j]->present || regions[i]->bar != regions[j]->bar) continue;
            const uint64_t begin_j = regions[j]->offset;
            const uint64_t end_j = begin_j + regions[j]->length;
            if (begin_i < end_j && begin_j < end_i) return -11;
        }
    }
    if ((out->notify.offset & 1u) != 0u) return -12;
    return 0;
}
