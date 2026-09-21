#pragma once
#include <stdint.h>
#define KORONOS_ABI_VERSION 0x00010000u
#define KORONOS_BOOTINFO_MAGIC 0x4B4F524Fu
enum koronos_cpu_class { KORONOS_CPU_CISC=1, KORONOS_CPU_RISC=2, KORONOS_CPU_CHIMERA=3 };
enum koronos_x86_mode { KORONOS_X86_REAL16=0, KORONOS_X86_PROTECTED32=1, KORONOS_X86_LONG64=2, KORONOS_X86_COMPAT32=3, KORONOS_X86_V8086=4 };
struct koronos_cpu_features {
 uint32_t max_basic_leaf;
 uint32_t max_extended_leaf;
 uint32_t family_model_stepping;
 uint32_t logical_cpus;
 uint8_t apic;
 uint8_t x2apic;
 uint8_t hypervisor;
 uint8_t long_mode;
 uint8_t nx;
 uint8_t sse2;
 uint8_t vmx;
 uint8_t svm;
 uint8_t invariant_tsc;
 uint8_t reserved[3];
 char vendor[13];
};
struct koronos_boot_context {
 uint32_t magic; uint32_t version; uint64_t boot_info; uint64_t kernel_base; uint64_t kernel_end;
 uint64_t module_base; uint64_t module_size; uint32_t cpu_class; uint32_t cpu_mode; uint64_t io_base; uint64_t reserved[3];
};
#ifdef __cplusplus
extern "C" {
#endif
void koronos_boot(const struct koronos_boot_context *ctx);
void koronos_arch_init(const struct koronos_boot_context *ctx);
void koronos_elf64_init(void);
void koronos_module_init(void);
const struct koronos_cpu_features* koronos_get_cpu_features(void);
void koronos_idle_loop(void);
#ifdef __cplusplus
}
#endif
