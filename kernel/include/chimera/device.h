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
 chimera_device_class device_class;
 char name[64];
} chimera_device;
typedef struct chimera_device_inventory { uint32_t count; chimera_device devices[CHIMERA_DEVICE_MAX]; } chimera_device_inventory;
int chimera_hardware_enumerate_devices(chimera_device_inventory *out);
const chimera_device_inventory *chimera_hardware_inventory(void);
int chimera_hardware_device_class(uint8_t base_class, uint8_t subclass);
#ifdef __cplusplus
}
#endif
