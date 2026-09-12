#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Bus { Unknown, Pci, Pcie, Usb, Nvme, Sata, Virtio, I2c, Spi, Gpio, Bluetooth }
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Class { Unknown, Cpu, Gpu, Network, Storage, Audio, Input, Display, Camera, Printer }
#[derive(Clone, Copy, Debug)]
pub struct Device { pub vendor: u16, pub device: u16, pub bus: Bus, pub class: Class, pub family: &'static str, pub stack: &'static str }

pub const BUILTIN: &[Device] = &[
    Device { vendor: 0x10DE, device: 0, bus: Bus::Pcie, class: Class::Gpu, family: "NVIDIA", stack: "nouveau/vendor-adapter" },
    Device { vendor: 0x1002, device: 0, bus: Bus::Pcie, class: Class::Gpu, family: "AMD", stack: "amdgpu/radeon" },
    Device { vendor: 0x8086, device: 0, bus: Bus::Pcie, class: Class::Gpu, family: "Intel", stack: "i915/xe" },
    Device { vendor: 0x1AF4, device: 0, bus: Bus::Virtio, class: Class::Gpu, family: "virtio", stack: "virtio-gpu" },
];
