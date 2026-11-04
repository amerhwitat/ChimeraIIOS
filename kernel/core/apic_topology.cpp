#include "chimera/apic_topology.h"

namespace {
uint32_t read_u32_le(const uint8_t *p) {
    return static_cast<uint32_t>(p[0]) |
           (static_cast<uint32_t>(p[1]) << 8) |
           (static_cast<uint32_t>(p[2]) << 16) |
           (static_cast<uint32_t>(p[3]) << 24);
}
}

extern "C" int koronos_apic_topology_parse_madt(
    const void *data, uint32_t length, uint32_t bsp_apic_id,
    koronos_apic_topology *out) {
    if (data == nullptr || out == nullptr || length > 1024u * 1024u) {
        return -1;
    }

    *out = {};
    out->abi = KORONOS_APIC_TOPOLOGY_ABI;
    out->bsp_apic_id = bsp_apic_id;
    out->bsp_index = UINT32_MAX;

    const auto *bytes = static_cast<const uint8_t *>(data);
    uint32_t offset = 0;
    while (offset < length) {
        if (length - offset < 2u) {
            return -2;
        }

        const uint8_t type = bytes[offset];
        const uint8_t size = bytes[offset + 1u];
        if (size < 2u || size > length - offset) {
            return -3;
        }

        uint32_t apic_id = 0;
        uint32_t acpi_uid = 0;
        uint32_t flags = 0;
        bool is_processor = false;

        if (type == 0u) {
            if (size != 8u) {
                return -4;
            }
            acpi_uid = bytes[offset + 2u];
            apic_id = bytes[offset + 3u];
            flags = read_u32_le(bytes + offset + 4u);
            is_processor = true;
        } else if (type == 9u) {
            if (size != 16u) {
                return -5;
            }
            apic_id = read_u32_le(bytes + offset + 4u);
            flags = read_u32_le(bytes + offset + 8u);
            acpi_uid = read_u32_le(bytes + offset + 12u);
            is_processor = true;
            out->x2apic_present = 1u;
        }

        /* Bit 0 means enabled; bit 1 means online-capable. Retain both,
         * but only enabled processors count as currently enabled. */
        if (is_processor && (flags & 3u) != 0u) {
            for (uint32_t i = 0; i < out->count; ++i) {
                if (out->cpus[i].apic_id == apic_id) {
                    return -6;
                }
            }
            if (out->count >= KORONOS_APIC_MAX_CPUS) {
                return -7;
            }

            koronos_apic_cpu &cpu = out->cpus[out->count];
            cpu.apic_id = apic_id;
            cpu.acpi_uid = acpi_uid;
            cpu.flags = flags;
            cpu.source_type = type;
            cpu.enabled = (flags & 1u) != 0u ? 1u : 0u;
            if (cpu.enabled) {
                ++out->enabled_count;
                if (apic_id == bsp_apic_id) {
                    out->bsp_index = out->count;
                }
            }
            ++out->count;
        }
        offset += size;
    }

    if (offset != length) {
        return -2;
    }
    if (out->bsp_index == UINT32_MAX) {
        return -8;
    }
    return 0;
}
