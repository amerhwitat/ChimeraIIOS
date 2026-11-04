#ifndef CHIMERA_KERNEL_ENTRY_H
#define CHIMERA_KERNEL_ENTRY_H
#include <stdint.h>
#include "../../boot/include/chimera/bootinfo.h"
#ifdef __cplusplus
extern "C" {
#endif
void koronos_boot_entry(const chm_bootinfo_t *bootinfo);
#ifdef __cplusplus
}
#endif
#endif
