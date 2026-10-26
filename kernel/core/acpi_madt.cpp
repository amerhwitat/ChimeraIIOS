#include "chimera/acpi_madt.h"
#include <stddef.h>
#include <stdint.h>

namespace {
static uint32_t rd32(const uint8_t *p) {
  return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
         ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static uint64_t rd64(const uint8_t *p) {
  return (uint64_t)rd32(p) | ((uint64_t)rd32(p + 4) << 32);
}
static bool signature(const uint8_t *p, const char *s) {
  return p[0] == (uint8_t)s[0] && p[1] == (uint8_t)s[1] &&
         p[2] == (uint8_t)s[2] && p[3] == (uint8_t)s[3];
}
static bool checksum_ok(const uint8_t *p, uint32_t n) {
  uint8_t sum = 0;
  for (uint32_t i = 0; i < n; ++i) sum = (uint8_t)(sum + p[i]);
  return sum == 0;
}
static bool add_cpu(koronos_acpi_topology *out, uint32_t uid,
                    uint32_t apic, uint32_t flags, bool x2) {
  const bool enabled = (flags & KORONOS_ACPI_CPU_ENABLED) != 0;
  const bool capable = (flags & KORONOS_ACPI_CPU_ONLINE_CAPABLE) != 0;
  /* Keep disabled-but-online-capable records for topology reporting, but never
   * claim they are online: only AP-written startup acknowledgements can do that. */
  if (!enabled && !capable) return true;
  for (uint32_t i = 0; i < out->count; ++i) {
    if (out->cpus[i].apic_id == apic) return false;
    if (out->cpus[i].acpi_processor_id == uid) return false;
  }
  if (out->count >= KORONOS_ACPI_MAX_CPUS) return false;
  koronos_acpi_cpu &cpu = out->cpus[out->count++];
  cpu.acpi_processor_id = uid;
  cpu.apic_id = apic;
  cpu.flags = flags;
  cpu.x2apic = x2 ? 1u : 0u;
  cpu.enabled = enabled ? 1u : 0u;
  cpu.online_capable = capable ? 1u : 0u;
  cpu.reserved = 0;
  if (enabled) ++out->enabled_count;
  if (capable) ++out->online_capable_count;
  return true;
}
}

extern "C" int koronos_acpi_madt_parse(const void *mapped_table,
                                        uint64_t mapped_bytes,
                                        koronos_acpi_topology *out) {
  if (!out) return -1;
  *out = {};
  if (!mapped_table || mapped_bytes < 44u) return -2;
  const uint8_t *p = static_cast<const uint8_t *>(mapped_table);
  if (!signature(p, "APIC")) return -3;
  const uint32_t length = rd32(p + 4);
  if (length < 44u || (uint64_t)length > mapped_bytes) return -4;
  if (!checksum_ok(p, length)) return -5;

  out->local_apic_address = rd32(p + 36);
  out->madt_flags = rd32(p + 40);
  uint32_t off = 44u;
  while (off < length) {
    if (length - off < 2u) { *out = {}; return -6; }
    const uint8_t type = p[off], size = p[off + 1u];
    if (size < 2u || (uint32_t)size > length - off) { *out = {}; return -7; }
    if (type == 0u) {
      if (size < 8u) { *out = {}; return -8; }
      const uint32_t uid = p[off + 2u], apic = p[off + 3u];
      const uint32_t flags = rd32(p + off + 4u);
      if (!add_cpu(out, uid, apic, flags, false)) { *out = {}; return -9; }
    } else if (type == 9u) {
      if (size < 16u) { *out = {}; return -10; }
      const uint32_t apic = rd32(p + off + 4u);
      const uint32_t flags = rd32(p + off + 8u);
      const uint32_t uid = rd32(p + off + 12u);
      if (!add_cpu(out, uid, apic, flags, true)) { *out = {}; return -11; }
    } else if (type == 5u) {
      /* Local APIC Address Override: 12 bytes, 64-bit address at +4. */
      if (size < 12u) { *out = {}; return -12; }
      const uint64_t address = rd64(p + off + 4u);
      if (address > UINT32_MAX) { *out = {}; return -13; }
      out->local_apic_address = (uint32_t)address;
    }
    off += size;
  }
  if (out->enabled_count == 0u) { *out = {}; return -14; }
  return 0;
}
