#pragma once
#include <stdint.h>
#include "chimera/multiboot_modules.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum chimera_boot_target {
    CHIMERA_BOOT_TARGET_INVALID = 0,
    CHIMERA_BOOT_TARGET_LIVE = 1,
    CHIMERA_BOOT_TARGET_INSTALLER = 2,
    CHIMERA_BOOT_TARGET_RECOVERY = 3
} chimera_boot_target;

typedef enum chimera_boot_target_error {
    CHIMERA_BOOT_TARGET_OK = 0,
    CHIMERA_BOOT_TARGET_ERR_UNKNOWN = -1,
    CHIMERA_BOOT_TARGET_ERR_MISSING_PAYLOAD = -2,
    CHIMERA_BOOT_TARGET_ERR_CONFLICTING_PAYLOADS = -3,
    CHIMERA_BOOT_TARGET_ERR_EMPTY_MODULE = -4,
    CHIMERA_BOOT_TARGET_ERR_NOT_SELECTED = -5,
    CHIMERA_BOOT_TARGET_ERR_DUPLICATE = -6
} chimera_boot_target_error;

/*
 * Validate an explicitly selected boot target against the Multiboot module
 * registry. This is admission only: success does not mean the payload has been
 * loaded as a process or entered at ring 3.
 */
int chimera_boot_target_validate(chimera_boot_target target);
/* Accept exactly one token: chimera.target=live|installer|recovery. */
int chimera_boot_target_parse(const char *command_line, chimera_boot_target *out_target);

#ifdef __cplusplus
}
#endif
