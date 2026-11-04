#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define KORONOS_APIC_TOPOLOGY_ABI 1u
#define KORONOS_APIC_MAX_CPUS 256u
typedef struct koronos_apic_cpu {
    uint32_t apic_id;
    uint32_t acpi_uid;
    uint32_t flags;
    uint8_t source_type;
    uint8_t enabled;
    uint8_t reserved[2];
} koronos_apic_cpu;
typedef struct koronos_apic_topology {
    uint32_t abi;
    uint32_t count;
    uint32_t enabled_count;
    uint32_t bsp_index;
    uint32_t bsp_apic_id;
    uint32_t x2apic_present;
    koronos_apic_cpu cpus[KORONOS_APIC_MAX_CPUS];
} koronos_apic_topology;
/* Parse the MADT entry stream (bytes after the fixed MADT header).
 * This discovers processors only; it does not start APs or mark them online. */
int koronos_apic_topology_parse_madt(const void *entries, uint32_t length,
                                     uint32_t bsp_apic_id,
                                     koronos_apic_topology *out);
#ifdef __cplusplus
}
#endif
