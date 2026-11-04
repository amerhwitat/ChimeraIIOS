#pragma once
#include <stdint.h>
#include "chimera/hardware.h"
#ifdef __cplusplus
extern "C" {
#endif
#define KORONOS_CPU_ARCH_REGISTRY_ABI 1u
const koronos_cpu_arch_descriptor *koronos_cpu_arch_find(const char *id);
const koronos_cpu_arch_descriptor *koronos_cpu_arch_at(uint32_t index);
uint32_t koronos_cpu_arch_count(void);
const koronos_cpu_arch_descriptor *koronos_cpu_arch_current(void);
#ifdef __cplusplus
}
#endif
