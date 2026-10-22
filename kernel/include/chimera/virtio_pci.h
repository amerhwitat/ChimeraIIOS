#pragma once
#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define KORONOS_VIRTIO_PCI_CONFIG_SPACE_SIZE 256u
#define KORONOS_VIRTIO_PCI_CAP_VENDOR_ID 0x09u

typedef struct koronos_virtio_pci_region {
    uint32_t offset;
    uint32_t length;
    uint8_t bar;
    uint8_t present;
    uint16_t reserved;
} koronos_virtio_pci_region;

typedef struct koronos_virtio_pci_caps {
    koronos_virtio_pci_region common;
    koronos_virtio_pci_region notify;
    koronos_virtio_pci_region isr;
    koronos_virtio_pci_region device;
    uint32_t notify_multiplier;
    uint8_t has_notify_multiplier;
    uint8_t reserved[3];
} koronos_virtio_pci_caps;

/* Parses a captured 256-byte PCI configuration header only. It does not
 * size or map BARs, enable bus mastering, or access MMIO. Returns 0 on a
 * valid modern Virtio PCI function, negative on malformed/unsupported input. */
int koronos_virtio_pci_parse_caps(const uint8_t config[KORONOS_VIRTIO_PCI_CONFIG_SPACE_SIZE],
                                 koronos_virtio_pci_caps *out);

#ifdef __cplusplus
}
#endif
