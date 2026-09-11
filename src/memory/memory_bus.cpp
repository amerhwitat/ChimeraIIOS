#include "chimera/memory_bus.hpp"
#include <algorithm>
#include <limits>
namespace chimera::memory {
namespace {
constexpr uint32_t kFaultInvalid = 1;
constexpr uint32_t kFaultAddressWidth = 2;
constexpr uint32_t kFaultUnmapped = 3;
constexpr uint32_t kFaultPermission = 4;
constexpr uint32_t kFaultDma = 5;
constexpr uint32_t kFaultMmioHandler = 6;
bool range_ok(uint64_t base, uint64_t size, uint64_t address, uint32_t width, uint8_t bits) {
    if (size == 0 || width == 0 || address < base) return false;
    const uint64_t max_addr = bits >= 64 ? std::numeric_limits<uint64_t>::max() : ((uint64_t{1} << bits) - 1);
    const uint64_t last = address + static_cast<uint64_t>(width) - 1;
    if (last < address || last > max_addr) return false;
    const uint64_t end = base + size - 1;
    return end >= base && last <= end;
}
}
VirtualMemoryBus::VirtualMemoryBus(BusSnapshot snapshot) : snapshot_(snapshot) {}
bool VirtualMemoryBus::add_region(MemoryRegion region, MmioHandler handler) {
    if (region.size == 0) return false;
    if (region.kind == RegionKind::Mmio && !handler) return false;
    for (const auto& mapping : mappings_) {
        const uint64_t a = mapping.region.base;
        const uint64_t b = a + mapping.region.size;
        const uint64_t c = region.base;
        const uint64_t d = c + region.size;
        if (b < a || d < c || !(d <= a || b <= c)) return false;
    }
    mappings_.push_back({region, std::move(handler)});
    return true;
}
BusResult VirtualMemoryBus::transact(const BusTransaction& t) const {
    if (t.width_bytes == 0 || t.width_bytes > sizeof(uint64_t)) return {false, 0, kFaultInvalid};
    const auto max_addr = snapshot_.profile.address_bits >= 64 ? std::numeric_limits<uint64_t>::max() : ((uint64_t{1} << snapshot_.profile.address_bits) - 1);
    const uint64_t last = t.address + static_cast<uint64_t>(t.width_bytes) - 1;
    if (last < t.address || last > max_addr) return {false, 0, kFaultAddressWidth};
    for (const auto& mapping : mappings_) {
        if (!range_ok(mapping.region.base, mapping.region.size, t.address, t.width_bytes, snapshot_.profile.address_bits)) continue;
        if (t.access == Access::Execute && mapping.region.kind == RegionKind::Mmio) return {false, 0, kFaultPermission};
        if (mapping.region.kind == RegionKind::DmaWindow && !snapshot_.profile.dma) return {false, 0, kFaultDma};
        if (mapping.region.kind == RegionKind::Mmio) {
            const auto result = mapping.handler(t);
            return result.ok ? result : BusResult{false, 0, result.fault ? result.fault : kFaultMmioHandler};
        }
        return {true, t.access == Access::Write ? t.value : 0, 0};
    }
    return {false, 0, kFaultUnmapped};
}
std::optional<BusProfile> VirtualMemoryBus::profile_for(std::string_view a) noexcept {
    if (a == "x86" || a == "x86-64") return BusProfile{"x86-64", 64, 64, Endianness::Little, Ordering::AcquireRelease, 64, true, true, true};
    if (a == "arm" || a == "aarch64") return BusProfile{"aarch64", 48, 128, Endianness::Little, Ordering::AcquireRelease, 64, true, true, true};
    if (a == "riscv32" || a == "riscv64") return BusProfile{a, 64, 64, Endianness::Little, Ordering::AcquireRelease, 64, true, true, true};
    if (a == "power64") return BusProfile{"power64", 64, 128, Endianness::BiEndian, Ordering::AcquireRelease, 128, true, true, true};
    if (a == "mips64") return BusProfile{"mips64", 64, 64, Endianness::BiEndian, Ordering::AcquireRelease, 64, true, true, true};
    if (a == "sparc64") return BusProfile{"sparc64", 64, 64, Endianness::Big, Ordering::AcquireRelease, 64, true, true, true};
    if (a == "s390x") return BusProfile{"s390x", 64, 128, Endianness::Big, Ordering::AcquireRelease, 256, true, true, true};
    if (a == "loongarch64") return BusProfile{"loongarch64", 48, 64, Endianness::Little, Ordering::AcquireRelease, 64, true, true, true};
    if (a == "m68k") return BusProfile{"m68k", 32, 32, Endianness::Big, Ordering::Sequential, 16, false, false, true};
    if (a == "avr") return BusProfile{"avr", 16, 8, Endianness::Little, Ordering::Sequential, 1, false, false, false};
    if (a == "xtensa") return BusProfile{"xtensa", 32, 64, Endianness::Little, Ordering::AcquireRelease, 32, true, true, true};
    if (a == "or1k") return BusProfile{"or1k", 32, 32, Endianness::Big, Ordering::AcquireRelease, 32, true, false, true};
    if (a == "alpha") return BusProfile{"alpha", 64, 64, Endianness::Little, Ordering::AcquireRelease, 64, true, true, true};
    if (a == "parisc64") return BusProfile{"parisc64", 64, 64, Endianness::Big, Ordering::AcquireRelease, 64, true, true, true};
    if (a == "sh4") return BusProfile{"sh4", 32, 32, Endianness::Little, Ordering::AcquireRelease, 32, true, false, true};
    if (a == "itanium") return BusProfile{"itanium", 64, 128, Endianness::Little, Ordering::AcquireRelease, 64, true, true, true};
    if (a == "r8192" || a == "chimera-r8192") return BusProfile{"chimera-r8192", 64, 512, Endianness::Little, Ordering::Sequential, 128, true, true, true};
    if (a == "c8192" || a == "chimera-c8192") return BusProfile{"chimera-c8192", 64, 512, Endianness::Little, Ordering::Sequential, 128, true, true, true};
    return std::nullopt;
}
} // namespace chimera::memory
