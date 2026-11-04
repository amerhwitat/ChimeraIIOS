#pragma once
#include <stdint.h>
#include "chimera/hardware.h"
#ifdef __cplusplus
extern "C" {
#endif
#define KORONOS_CPU_ARCH_REGISTRY_ABI 1u
typedef struct koronos_cpu_arch_descriptor {
    const char *id;
    const char *class_name;
    uint16_t word_bits;
    uint8_t target_kind;
    uint8_t kernel_arch;
    uint8_t native_kernel;
    uint8_t detection_method;
} koronos_cpu_arch_descriptor;
const koronos_cpu_arch_descriptor *koronos_cpu_arch_find(const char *id);
const koronos_cpu_arch_descriptor *koronos_cpu_arch_at(uint32_t index);
uint32_t koronos_cpu_arch_count(void);
const koronos_cpu_arch_descriptor *koronos_cpu_arch_current(void);
#ifdef __cplusplus
}
#endif
