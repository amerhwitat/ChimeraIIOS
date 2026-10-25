#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef const uint8_t *(*koronos_acpi_map_fn)(uint64_t physical_address, uint64_t bytes, void *context);
/* The callback must return a readable mapping covering the entire requested range,
 * or nullptr. This code never casts a physical address directly to a pointer. */
int koronos_acpi_find_rsdp(koronos_acpi_map_fn map, void *context, uint64_t *rsdp_phys);
int koronos_acpi_locate_madt(koronos_acpi_map_fn map, void *context,
                              uint64_t rsdp_phys, uint64_t *madt_phys);
#ifdef __cplusplus
}
#endif
