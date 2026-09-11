#pragma once
#include <cstdint>

namespace chimera::mobile {

enum class DeviceClass : std::uint8_t {
    Display, Input, Gpu, Audio, Camera, Sensor, Storage,
    Usb, Bluetooth, Wifi, Cellular, Power, Iommu
};

struct DeviceDescriptor {
    std::uint64_t id{};
    DeviceClass type{DeviceClass::Input};
    std::uint64_t capability_object{};
};

class DriverEndpoint {
public:
    bool attach(const DeviceDescriptor& device) noexcept {
        attached_ = device.id != 0 && device.capability_object != 0;
        return attached_;
    }
    bool attached() const noexcept { return attached_; }

private:
    bool attached_{false};
};

} // namespace chimera::mobile
