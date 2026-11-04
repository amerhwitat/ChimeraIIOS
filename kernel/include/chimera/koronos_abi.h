#pragma once
#include <stdint.h>
#define KORONOS_ABI_VERSION 0x00010000u
#define KORONOS_BOOTINFO_MAGIC 0x4B4F524Fu
enum koronos_cpu_class { KORONOS_CPU_CISC=1, KORONOS_CPU_RISC=2, KORONOS_CPU_CHIMERA=3 };
enum koronos_arch_id {
 KORONOS_ARCH_UNKNOWN=0, KORONOS_ARCH_X86=1, KORONOS_ARCH_X86_64=2,
 KORONOS_ARCH_ARM=3, KORONOS_ARCH_AARCH64=4, KORONOS_ARCH_RISCV32=5,
 KORONOS_ARCH_RISCV64=6, KORONOS_ARCH_POWERPC=7, KORONOS_ARCH_MIPS=8,
 KORONOS_ARCH_SPARC=9, KORONOS_ARCH_LOONGARCH=10, KORONOS_ARCH_S390=11,
 KORONOS_ARCH_ALPHA=12, KORONOS_ARCH_M68K=13, KORONOS_ARCH_ARC=14,
 KORONOS_ARCH_OPENRISC=15, KORONOS_ARCH_PARISC=16, KORONOS_ARCH_NIOS2=17,
 KORONOS_ARCH_MICROBLAZE=18, KORONOS_ARCH_XTENSA=19, KORONOS_ARCH_SUPERH=20,
 KORONOS_ARCH_CSKY=21, KORONOS_ARCH_HEXAGON=22
};
enum koronos_cpu_feature {
 KORONOS_CPU_FEAT_FPU=1ull<<0, KORONOS_CPU_FEAT_TSC=1ull<<1,
 KORONOS_CPU_FEAT_APIC=1ull<<2, KORONOS_CPU_FEAT_X2APIC=1ull<<3,
 KORONOS_CPU_FEAT_SSE2=1ull<<4, KORONOS_CPU_FEAT_NX=1ull<<5,
 KORONOS_CPU_FEAT_LONG_MODE=1ull<<6, KORONOS_CPU_FEAT_VMX=1ull<<7,
 KORONOS_CPU_FEAT_SVM=1ull<<8, KORONOS_CPU_FEAT_XSAVE=1ull<<9,
 KORONOS_CPU_FEAT_OSXSAVE=1ull<<10, KORONOS_CPU_FEAT_AVX=1ull<<11,
 KORONOS_CPU_FEAT_AVX2=1ull<<12, KORONOS_CPU_FEAT_SSE41=1ull<<13,
 KORONOS_CPU_FEAT_SSE42=1ull<<14, KORONOS_CPU_FEAT_AES=1ull<<15,
 KORONOS_CPU_FEAT_SMEP=1ull<<16, KORONOS_CPU_FEAT_SMAP=1ull<<17,
 KORONOS_CPU_FEAT_INVPCID=1ull<<18, KORONOS_CPU_FEAT_HYPERVISOR=1ull<<19,
 KORONOS_CPU_FEAT_INVARIANT_TSC=1ull<<20
};
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
 /* Extended, normalized identification. Unknown values remain zero. */
 uint32_t architecture;
 uint32_t implementer;
 uint32_t variant;
 uint32_t family;
 uint32_t model;
 uint32_t stepping;
 uint32_t processor_id;
 uint32_t physical_address_bits;
 uint32_t virtual_address_bits;
 uint64_t feature_flags;
 uint64_t xcr0;
 uint64_t architecture_features[3];
 char brand[49];
 uint32_t backend_status;
 uint8_t entry_backend_present;
 uint8_t interrupt_backend_present;
 uint8_t syscall_backend_present;
 uint8_t backend_reserved;
};
struct koronos_boot_context {
 uint32_t magic; uint32_t version; uint64_t boot_info; uint64_t kernel_base; uint64_t kernel_end;
 uint64_t module_base; uint64_t module_size; uint32_t cpu_class; uint32_t cpu_mode; uint64_t io_base; uint32_t detected_cores; uint32_t compatibility_mode; uint64_t reserved[2];
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
