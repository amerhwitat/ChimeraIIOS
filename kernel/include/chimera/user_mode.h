#pragma once
#include "chimera/elf_loader.h"
#ifdef __cplusplus
extern "C" {
#endif
/* Initializes the x86-64 bootstrap identity map, user selectors, TSS and IDT. */
int chimera_x86_64_user_mode_init(void);
const chimera_elf_loader_ops *chimera_x86_64_user_loader_ops(void);
#ifdef __cplusplus
}
#endif
