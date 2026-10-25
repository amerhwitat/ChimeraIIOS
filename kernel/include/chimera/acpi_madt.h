#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define KORONOS_ACPI_MAX_CPUS 32u
#define KORONOS_ACPI_CPU_ENABLED 0x01u
#define KORONOS_ACPI_CPU_ONLINE_CAPABLE 0x02u
typedef struct koronos_acpi_cpu {
  uint32_t acpi_processor_id;
  uint32_t apic_id;
  uint32_t flags;
  uint8_t x2apic;
  uint8_t enabled;
  uint8_t online_capable;
  uint8_t reserved;
} koronos_acpi_cpu;
typedef struct koronos_acpi_topology {
  uint32_t count;
  uint32_t enabled_count;
  uint32_t online_capable_count;
  uint32_t local_apic_address;
  uint32_t madt_flags;
  koronos_acpi_cpu cpus[KORONOS_ACPI_MAX_CPUS];
} koronos_acpi_topology;
/* Parse an already mapped, readable ACPI MADT byte range. This function does
 * not dereference physical addresses or establish that a physical mapping is safe.
 * Returns 0 on success; negative values indicate malformed input or capacity. */
int koronos_acpi_madt_parse(const void *mapped_table, uint64_t mapped_bytes,
                            koronos_acpi_topology *out);
#ifdef __cplusplus
}
#endif
