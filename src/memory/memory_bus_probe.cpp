#include "chimera/memory_bus_probe.hpp"
namespace chimera::memory {
std::optional<BusSnapshot> inspect_bus(const ProbeInput& in) noexcept {
    if (in.architecture.empty() || in.address_bits == 0 || in.address_bits > 64 || in.data_bits == 0) return std::nullopt;
    if (in.cache_line_bytes == 0 || (in.cache_line_bytes & (in.cache_line_bytes - 1)) != 0) return std::nullopt;
    if (in.cpu_count == 0 || in.numa_nodes == 0) return std::nullopt;
    return BusSnapshot{BusProfile{in.architecture, in.address_bits, in.data_bits, in.endianness, in.ordering, in.cache_line_bytes, in.coherent, in.iommu, in.dma}, in.ram_bytes, in.mmio_bytes, in.dma_bytes, in.cpu_count, in.numa_nodes, in.firmware_flags, in.hypervisor_flags};
}
}
