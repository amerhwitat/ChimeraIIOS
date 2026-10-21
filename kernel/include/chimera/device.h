#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_DEVICE_MAX 256u
typedef enum chimera_device_class : uint32_t { CHM_DEV_UNKNOWN=0, CHM_DEV_STORAGE=1, CHM_DEV_NETWORK=2, CHM_DEV_MOTHERBOARD=3, CHM_DEV_DISPLAY=4, CHM_DEV_GPU=5, CHM_DEV_USB=6, CHM_DEV_OTHER=7 } chimera_device_class;
typedef struct chimera_device {
 uint32_t bus, domain, bdf, class_code, subclass, prog_if, revision;
 uint16_t vendor_id, device_id, subsystem_vendor, subsystem_device;
 uint32_t flags;
 /* Raw PCI BAR dwords as observed; not sized, mapped, or safe to dereference. */
 uint8_t bar_count;
 uint8_t bar_reserved[3];
 uint32_t bar_raw[6];
 chimera_device_class device_class;
 char name[64];
} chimera_device;
typedef struct chimera_device_inventory { uint32_t count; chimera_device devices[CHIMERA_DEVICE_MAX]; } chimera_device_inventory;

/* Decoded BAR address/type only; this does not size, reserve, or map the BAR. */
typedef enum chimera_pci_bar_kind : uint8_t {
 CHM_PCI_BAR_INVALID=0, CHM_PCI_BAR_IO=1, CHM_PCI_BAR_MMIO20=2,
 CHM_PCI_BAR_MMIO32=3, CHM_PCI_BAR_MMIO64=4
} chimera_pci_bar_kind;
typedef struct chimera_pci_bar {
 uint64_t address;
 chimera_pci_bar_kind kind;
 uint8_t prefetchable;
 uint8_t consumes_next;
 uint8_t reserved;
} chimera_pci_bar;
int chimera_pci_decode_bar(uint32_t low, uint32_t high, chimera_pci_bar *out);
int chimera_hardware_enumerate_devices(chimera_device_inventory *out);
const chimera_device_inventory *chimera_hardware_inventory(void);
int chimera_hardware_device_class(uint8_t base_class, uint8_t subclass);
#ifdef __cplusplus
}
#endif
