#pragma once
#include <cstdint>
#include <string_view>

namespace chm::drivers {

enum class Bus : uint8_t { Unknown, PCI, PCIE, USB, NVMe, SATA, Virtio, I2C, SPI, GPIO, Bluetooth };
enum class Class : uint8_t { Unknown, CPU, GPU, Network, Storage, Audio, Input, Display, Camera, Printer };
struct Device { uint16_t vendor; uint16_t device; Bus bus; Class klass; std::string_view family; std::string_view stack; };

constexpr Device kBuiltinDevices[] = {
    {0x10DE, 0, Bus::PCIE, Class::GPU, "NVIDIA", "nouveau/vendor-adapter"},
    {0x1002, 0, Bus::PCIE, Class::GPU, "AMD", "amdgpu/radeon"},
    {0x8086, 0, Bus::PCIE, Class::GPU, "Intel", "i915/xe"},
    {0x1AF4, 0, Bus::Virtio, Class::GPU, "virtio", "virtio-gpu"},
    {0x1AF4, 0, Bus::Virtio, Class::Network, "virtio", "virtio-net"},
    {0x1AF4, 0, Bus::Virtio, Class::Storage, "virtio", "virtio-blk"},
};

constexpr std::size_t builtin_device_count() { return sizeof(kBuiltinDevices) / sizeof(kBuiltinDevices[0]); }

} // namespace chm::drivers
