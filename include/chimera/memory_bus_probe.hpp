#pragma once
#include "chimera/memory_bus.hpp"
#include <cstdint>
#include <string_view>
namespace chimera::memory {
struct ProbeInput {
    std::string_view architecture{};
    uint8_t address_bits{};
    uint16_t data_bits{};
    Endianness endianness{Endianness::Little};
    Ordering ordering{Ordering::Relaxed};
    uint16_t cache_line_bytes{};
    bool coherent{};
    bool iommu{};
    bool dma{};
    uint64_t ram_bytes{};
    uint64_t mmio_bytes{};
    uint64_t dma_bytes{};
    uint32_t cpu_count{1};
    uint32_t numa_nodes{1};
    uint64_t firmware_flags{};
    uint64_t hypervisor_flags{};
};
std::optional<BusSnapshot> inspect_bus(const ProbeInput& input) noexcept;
}
