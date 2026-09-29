#pragma once
#include <stdint.h>
#include "chimera/koronos_abi.h"
#ifdef __cplusplus
extern "C" {
#endif
enum chimera_module_kind { CHIMERA_MODULE_UNKNOWN=0, CHIMERA_MODULE_LIVE_INITRAMFS=1, CHIMERA_MODULE_LIVE_MANIFEST=2, CHIMERA_MODULE_INSTALL_IMAGE=3, CHIMERA_MODULE_INSTALL_MANIFEST=4, CHIMERA_MODULE_INSTALL_CONTRACT=5, CHIMERA_MODULE_INSTALL_PHASES=6, CHIMERA_MODULE_INSTALL_PROFILES=7, CHIMERA_MODULE_OTHER=8 };
typedef struct { uint64_t base,size; uint32_t kind; char cmdline[128]; } chimera_boot_module;
uint32_t chimera_multiboot_scan(uint64_t boot_info);
uint32_t chimera_multiboot_module_count(void);
const chimera_boot_module* chimera_multiboot_module(uint32_t index);
const chimera_boot_module* chimera_multiboot_find(uint32_t kind);
#ifdef __cplusplus
}
#endif
