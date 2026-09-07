#pragma once
#include <stdint.h>
#define CHM_BOOTINFO_MAGIC 0x43484D42u
#define CHM_BOOTINFO_VERSION 4u
typedef enum { CHM_ARCH_UNKNOWN=0, CHM_ARCH_X86_64, CHM_ARCH_ARM64, CHM_ARCH_RISCV64, CHM_ARCH_CHIMERA_R8192, CHM_ARCH_CHIMERA_C8192 } chm_arch_t;
typedef enum { CHM_ENC_FIXED=0, CHM_ENC_VARIABLE=1 } chm_encoding_t;
typedef struct { chm_arch_t arch; chm_encoding_t encoding; uint16_t gpr_bits; uint16_t vector_bits; uint32_t lanes; uint64_t features; uint8_t endian; uint8_t firmware_mode; uint16_t reserved; } chm_cpu_profile_t;
typedef struct { uint32_t magic, version, size, crc32; chm_cpu_profile_t cpu; uint64_t mmap_addr; uint32_t mmap_count; uint32_t flags; uint64_t acpi_rsdp; uint64_t efi_system_table; uint64_t framebuffer_addr; uint32_t fb_pitch, fb_width, fb_height; uint8_t fb_bpp, fb_format; uint16_t reserved; uint64_t initrd_addr, initrd_size; uint64_t cmdline_addr; } chm_bootinfo_t;
