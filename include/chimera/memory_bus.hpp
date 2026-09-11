#pragma once
#include <cstdint>
#include <functional>
#include <optional>
#include <string_view>
#include <vector>
namespace chimera::memory {
enum class Endianness : uint8_t { Little, Big, BiEndian };
enum class Ordering : uint8_t { Relaxed, AcquireRelease, Sequential };
enum class RegionKind : uint8_t { Ram, Mmio, Reserved, DmaWindow };
enum class Access : uint8_t { Read, Write, Execute };
struct BusProfile { std::string_view architecture{}; uint8_t address_bits{64}; uint16_t data_bits{64}; Endianness endianness{Endianness::Little}; Ordering ordering{Ordering::Relaxed}; uint16_t cache_line_bytes{64}; bool coherent{true}; bool iommu{false}; bool dma{true}; };
struct BusSnapshot { BusProfile profile{}; uint64_t ram_bytes{}; uint64_t mmio_bytes{}; uint64_t dma_bytes{}; uint32_t cpu_count{1}; uint32_t numa_nodes{1}; uint64_t firmware_flags{}; uint64_t hypervisor_flags{}; };
struct MemoryRegion { uint64_t base{}; uint64_t size{}; RegionKind kind{RegionKind::Reserved}; uint32_t attributes{}; };
struct BusTransaction { uint64_t address{}; uint32_t width_bytes{1}; Access access{Access::Read}; Endianness endianness{Endianness::Little}; Ordering ordering{Ordering::Relaxed}; uint64_t value{}; };
struct BusResult { bool ok{false}; uint64_t value{}; uint32_t fault{}; };
class VirtualMemoryBus {
public:
 using MmioHandler = std::function<BusResult(const BusTransaction&)>;
 explicit VirtualMemoryBus(BusSnapshot snapshot);
 bool add_region(MemoryRegion region, MmioHandler handler = {});
 BusResult transact(const BusTransaction& transaction) const;
 const BusSnapshot& snapshot() const noexcept { return snapshot_; }
 std::size_t region_count() const noexcept { return mappings_.size(); }
 static std::optional<BusProfile> profile_for(std::string_view architecture) noexcept;
private:
 struct Mapping { MemoryRegion region; MmioHandler handler; };
 BusSnapshot snapshot_{};
 std::vector<Mapping> mappings_{};
};
}
