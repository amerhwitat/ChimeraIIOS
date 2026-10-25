#include "chimera/firmware.h"
#include "chimera/koronos_abi.h"
#include <stddef.h>
#include <stdint.h>

/* Multiboot2 tags are byte streams supplied by the bootloader. Do not use
 * unaligned typed loads or unchecked offset+size arithmetic while walking them. */
struct mb2_tag { uint32_t type, size; };

static uint32_t read32le(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static uint64_t read64le(const uint8_t *p) {
    return (uint64_t)read32le(p) | ((uint64_t)read32le(p + 4) << 32);
}
static bool has_bytes(uint32_t total, uint32_t off, uint32_t n) {
    return off <= total && n <= total - off;
}

extern "C" int chimera_firmware_probe(const void *boot_context,
                                       chimera_firmware_profile *out) {
    if (!out) return -1;
    for (size_t i = 0; i < sizeof(*out); ++i)
        reinterpret_cast<uint8_t *>(out)[i] = 0;
    out->version = CHIMERA_FIRMWARE_VERSION;

    const koronos_boot_context *ctx =
        static_cast<const koronos_boot_context *>(boot_context);
    if (!ctx || ctx->magic != KORONOS_BOOTINFO_MAGIC ||
        ctx->version != KORONOS_ABI_VERSION) return -2;
    const uint8_t *base = reinterpret_cast<const uint8_t *>(
        static_cast<uintptr_t>(ctx->boot_info));
    if (!base) return -3;

    /* The bootloader owns this Multiboot2 block. total_size bounds all parsing;
     * this cannot make an invalid physical pointer safe, so the caller must
     * still pass a boot_info address covered by the active boot memory map. */
    const uint32_t total = read32le(base);
    if (total < 16u) return -4;
    uint32_t off = 8u;
    bool ended = false;
    while (has_bytes(total, off, 8u)) {
        const uint32_t type = read32le(base + off);
        const uint32_t size = read32le(base + off + 4u);
        if (size < 8u || !has_bytes(total, off, size)) return -5;
        if (type == 0u) {
            if (size != 8u) return -6;
            ended = true;
            break;
        }

        const uint8_t *payload = base + off + 8u;
        const uint32_t payload_size = size - 8u;
        if (type == 11u || type == 12u) {
            if (payload_size < 8u) return -7;
            out->type = CHIMERA_FW_UEFI;
            out->efi_system_table = read64le(payload);
            out->runtime_services = 1u;
        } else if (type == 14u || type == 15u) {
            /* ACPI RSDP v1 is 20 bytes; v2+ has a 36-byte fixed prefix. */
            const uint32_t need = type == 15u ? 36u : 20u;
            if (payload_size < need) return -8;
            out->acpi_rsdp = (uint64_t)(uintptr_t)payload;
            out->acpi_revision = type == 15u ? 2u : 1u;
        } else if (type == 13u) {
            if (payload_size < 8u) return -9;
            out->smbios_major = payload[0];
            out->smbios_minor = payload[1];
            out->smbios_entry = (uint64_t)(uintptr_t)(payload + 8u);
        }

        /* Multiboot2 tags are padded to an 8-byte boundary. Avoid wraparound
         * and reject a final padding span that exceeds total_size. */
        if (size > UINT32_MAX - 7u) return -10;
        const uint32_t aligned = (size + 7u) & ~7u;
        if (!has_bytes(total, off, aligned)) return -11;
        off += aligned;
    }
    if (!ended) return -12;
    if (out->type == CHIMERA_FW_UNKNOWN) out->type = CHIMERA_FW_BIOS;
    return 0;
}

extern "C" int chimera_firmware_validate_tables(
    const chimera_firmware_profile *p) {
    if (!p || p->version != CHIMERA_FIRMWARE_VERSION) return -1;
    if (p->type == CHIMERA_FW_UEFI && !p->efi_system_table) return -2;
    return 0;
}
