#pragma once
#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <string_view>
#include <vector>
namespace chimera::memory {
enum class Endianness : std::uint8_t { Little, Big, BiEndian };
enum class Ordering : std::uint8_t { Relaxed, AcquireRelease, Sequential };
enum class RegionKind : std::uint8_t { Ram, Mmio, Reserved, DmaWindow };
enum class Access : std::uint8_t { Read, Write, Execute };
struct BusProfile { std::string_view architecture{}; std::uint8_t address_bits{64}; std::uint16_t data_bits{64}; Endianness endianness{Endianness::Little}; Ordering ordering{Ordering::Relaxed}; std::uint16_t cache_line_bytes{64}; bool coherent{true}; bool iommu{false}; bool dma{true}; };
struct BusSnapshot { BusProfile profile{}; std::uint64_t ram_bytes{}; std::uint64_t mmio_bytes{}; std::uint64_t dma_bytes{}; std::uint32_t cpu_count{1}; std::uint32_t numa_nodes{1}; std::uint64_t firmware_flags{}; std::uint64_t hypervisor_flags{}; };
struct MemoryRegion { std::uint64_t base{}; std::uint64_t size{}; RegionKind kind{RegionKind::Reserved}; std::uint32_t attributes{}; };
struct BusTransaction { std::uint64_t address{}; std::uint32_t width_bytes{1}; Access access{Access::Read}; Endianness endianness{Endianness::Little}; Ordering ordering{Ordering::Relaxed}; std::uint64_t value{}; };
struct BusResult { bool ok{false}; std::uint64_t value{}; std::uint32_t fault{}; };
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
