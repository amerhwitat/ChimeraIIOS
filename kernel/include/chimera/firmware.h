#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_FIRMWARE_VERSION 1u
typedef enum chimera_firmware_type : uint32_t { CHIMERA_FW_UNKNOWN=0, CHIMERA_FW_BIOS=1, CHIMERA_FW_UEFI=2, CHIMERA_FW_UEFI_CSM=3 } chimera_firmware_type;
typedef struct chimera_firmware_profile {
  uint32_t version, type;
  uint64_t efi_system_table, acpi_rsdp, smbios_entry, dtb, tpm_event_log;
  uint32_t secure_boot, setup_mode, runtime_services, acpi_revision, smbios_major, smbios_minor;
  char vendor[64], version_string[64], board[96];
} chimera_firmware_profile;
int chimera_firmware_probe(const void *boot_context, chimera_firmware_profile *out);
int chimera_firmware_validate_tables(const chimera_firmware_profile *p);
#ifdef __cplusplus
}
#endif
