#ifndef CHIMERA_SF2_LOADER_H
#define CHIMERA_SF2_LOADER_H
#include <stdint.h>
#include "../include/chimera/bootinfo.h"
#ifdef __cplusplus
extern "C" {
#endif
void chm_sf2_entry(chm_bootinfo_t *bootinfo);
void sf2_entry_asm(void);
#ifdef __cplusplus
}
#endif
#endif
