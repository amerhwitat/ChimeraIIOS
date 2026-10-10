#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define KORONOS_DRIVER_ABI 0x00010000u
enum chimera_driver_bus : uint32_t { CHM_BUS_PCI=1, CHM_BUS_USB=2, CHM_BUS_ACPI=3, CHM_BUS_VIRTIO=4, CHM_BUS_PLATFORM=5, CHM_BUS_I2C=6, CHM_BUS_SPI=7, CHM_BUS_MMIO=8 };
enum chimera_driver_class : uint32_t { CHM_DRV_STORAGE=1, CHM_DRV_NET=2, CHM_DRV_WIFI=3, CHM_DRV_GPU=4, CHM_DRV_DISPLAY=5, CHM_DRV_INPUT=6, CHM_DRV_AUDIO=7, CHM_DRV_USB=8, CHM_DRV_FS=9, CHM_DRV_SENSOR=10, CHM_DRV_PLATFORM=11 };
/* state: 0=registered, 1=eligible, 2=matched/unprobed, 3=started, 5=probe failed. */
struct chimera_driver_descriptor { uint32_t abi_version; uint32_t bus; uint32_t device_class; uint32_t flags; uint16_t vendor_id; uint16_t device_id; uint32_t subsystem_id; const char* name; const char* firmware; const char* version; uint8_t match_class; uint8_t match_subclass; uint8_t match_prog_if; uint8_t state; const char* source; int (*probe)(const void* device); };
struct chimera_driver_registry { uint32_t count; uint32_t capacity; const chimera_driver_descriptor* entries; };
int chimera_driver_register(const chimera_driver_descriptor*);
const chimera_driver_registry* chimera_driver_registry_snapshot(void);
/* Returns the highest-scoring registered candidate for a bus/device tuple. */
const chimera_driver_descriptor* chimera_driver_best_match(const void* device, uint32_t bus);
int chimera_driver_probe_all(void);
int chimera_driver_start_all(void);
#ifdef __cplusplus
}
#endif
