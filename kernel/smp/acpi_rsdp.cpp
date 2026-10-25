#include "chimera/acpi_rsdp.h"
#include <stddef.h>
#include <stdint.h>

namespace {
constexpr uint64_t kMaxTable = 1024u * 1024u;
constexpr uint64_t kBiosStart = 0xE0000u;
constexpr uint64_t kBiosEnd = 0x100000u;
constexpr uint64_t kEbdaPointer = 0x40Eu;
constexpr uint64_t kRsdptrV1 = 20u;
constexpr uint64_t kRsdptrV2 = 36u;
constexpr uint64_t kHeaderSize = 36u;
static uint16_t le16(const uint8_t *p) { return (uint16_t)p[0] | ((uint16_t)p[1] << 8); }
static uint32_t le32(const uint8_t *p) {
  return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static uint64_t le64(const uint8_t *p) { return (uint64_t)le32(p) | ((uint64_t)le32(p + 4) << 32); }
static bool sig(const uint8_t *p, const char *s, size_t n) {
  for (size_t i = 0; i < n; ++i) if (p[i] != (uint8_t)s[i]) return false;
  return true;
}
static bool sum_ok(const uint8_t *p, uint64_t n) {
  uint8_t sum = 0; for (uint64_t i = 0; i < n; ++i) sum = (uint8_t)(sum + p[i]); return sum == 0;
}
static bool add_ok(uint64_t a, uint64_t b, uint64_t *out) {
  if (a > UINT64_MAX - b) return false; *out = a + b; return true;
}
static bool rsdp_at(koronos_acpi_map_fn map, void *ctx, uint64_t phys) {
  const uint8_t *p = map(phys, kRsdptrV1, ctx);
  if (!p || !sig(p, "RSD PTR ", 8) || !sum_ok(p, kRsdptrV1)) return false;
  if (p[15] < 2) return true;
  p = map(phys, kRsdptrV2, ctx);
  if (!p || le32(p + 20) < kRsdptrV2) return false;
  uint32_t len = le32(p + 20);
  if (len < kRsdptrV2 || len > 4096u) return false;
  p = map(phys, len, ctx);
  return p && sum_ok(p, len);
}
static bool scan(koronos_acpi_map_fn map, void *ctx, uint64_t start, uint64_t end, uint64_t *found) {
  for (uint64_t a = (start + 15u) & ~15ull; a <= end && end - a >= 20u; a += 16u) {
    if (rsdp_at(map, ctx, a)) { *found = a; return true; }
  }
  return false;
}
}
extern "C" int koronos_acpi_find_rsdp(koronos_acpi_map_fn map, void *context, uint64_t *rsdp_phys) {
  if (!rsdp_phys) return -1;
  *rsdp_phys = 0;
  if (!map) return -2;
  /* BDA 0x40e contains the EBDA segment. Search its first KiB, if plausible. */
  const uint8_t *bda = map(kEbdaPointer, 2, context);
  if (bda) {
    uint64_t ebda = (uint64_t)le16(bda) << 4;
    uint64_t ebda_end;
    if (ebda >= 0x400u && ebda < kBiosStart && add_ok(ebda, 1024u, &ebda_end) &&
        ebda_end <= kBiosStart && scan(map, context, ebda, ebda_end, rsdp_phys)) return 0;
  }
  if (scan(map, context, kBiosStart, kBiosEnd, rsdp_phys)) return 0;
  return -3;
}
extern "C" int koronos_acpi_locate_madt(koronos_acpi_map_fn map, void *context,
                                          uint64_t rsdp_phys, uint64_t *madt_phys) {
  if (!madt_phys) return -1;
  *madt_phys = 0;
  if (!map || !rsdp_phys) return -2;
  if (!rsdp_at(map, context, rsdp_phys)) return -3;
  const uint8_t *r = map(rsdp_phys, kRsdptrV1, context);
  if (!r) return -4;
  uint64_t root_phys = le32(r + 16);
  bool xsdt = false;
  if (r[15] >= 2) {
    const uint8_t *r2 = map(rsdp_phys, kRsdptrV2, context);
    if (!r2) return -5;
    uint64_t x = le64(r2 + 24);
    if (x) { root_phys = x; xsdt = true; }
  }
  if (!root_phys) return -6;
  const uint8_t *h = map(root_phys, kHeaderSize, context);
  if (!h || !sig(h, xsdt ? "XSDT" : "RSDT", 4)) return -7;
  uint32_t len = le32(h + 4);
  uint32_t width = xsdt ? 8u : 4u;
  if (len < kHeaderSize || len > kMaxTable || ((len - kHeaderSize) % width) != 0) return -8;
  h = map(root_phys, len, context);
  if (!h || !sum_ok(h, len)) return -9;
  uint32_t count = (len - (uint32_t)kHeaderSize) / width;
  for (uint32_t i = 0; i < count; ++i) {
    const uint8_t *slot = h + kHeaderSize + (uint64_t)i * width;
    uint64_t entry = xsdt ? le64(slot) : le32(slot);
    if (!entry) continue;
    const uint8_t *eh = map(entry, kHeaderSize, context);
    if (!eh) continue;
    if (!sig(eh, "APIC", 4)) continue;
    uint32_t mlen = le32(eh + 4);
    if (mlen < 44u || mlen > kMaxTable) continue;
    const uint8_t *m = map(entry, mlen, context);
    if (m && sum_ok(m, mlen)) { *madt_phys = entry; return 0; }
  }
  return -10;
}
