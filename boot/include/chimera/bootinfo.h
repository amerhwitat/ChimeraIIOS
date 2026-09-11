#ifndef CHIMERA_BOOTINFO_H
#define CHIMERA_BOOTINFO_H
#include <stdint.h>
#include "cpu_profile.h"
#include "boot_flags.h"
#define CHM_BOOTINFO_MAGIC 0x43484D42u
#define CHM_BOOTINFO_VERSION 4u
typedef struct { uint64_t base; uint64_t length; uint32_t type; uint32_t attributes; } chm_memory_region_t;
typedef struct {
    uint32_t magic, version, size, crc32;
    chm_cpu_profile_t cpu;
    uint64_t memory_map; uint32_t memory_map_count; uint32_t flags;
    uint64_t acpi_rsdp; uint64_t efi_system_table;
    uint64_t framebuffer_addr; uint32_t framebuffer_pitch, framebuffer_width, framebuffer_height;
    uint8_t framebuffer_bpp, framebuffer_format; uint16_t reserved0;
    uint64_t initrd_addr, initrd_size, cmdline_addr, boot_tsc;
    uint8_t tpm_pcr_digest[32];
} chm_bootinfo_t;
#ifdef __cplusplus
static_assert(sizeof(chm_cpu_profile_t) == 32, "CPU profile ABI drift");
static_assert(sizeof(chm_bootinfo_t) == 168, "bootinfo ABI drift");
#endif
#endif
