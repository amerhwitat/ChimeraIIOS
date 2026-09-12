# Driver Architecture and Hardware Coverage

## Source-informed architecture

Chimera II uses compatibility boundaries inspired by public driver ecosystems rather than copying proprietary or GPL-incompatible code. The implementation targets the concepts used by Linux's device/driver model, DRM/KMS, ALSA, V4L2, networking, Windows WDK/driver-model interfaces, Mesa graphics stacks, CUPS/OpenPrinting and SANE.

## Hardware coverage strategy

It is not technically maintainable to hard-code every model number forever. Instead, Chimera II stores stable **vendor/family/class capabilities** and supports generated PCI/USB ID catalogs. A generator can refresh IDs without changing kernel ABI.

### GPU families

NVIDIA, AMD, Intel, Apple, ARM Mali, Qualcomm Adreno, Imagination PowerVR, 3dfx, Matrox, S3, VIA, SiS and virtual GPU devices are represented. Compute adapters include CUDA/ROCm/Level-Zero style boundaries; graphics adapters expose Vulkan/OpenGL/OpenGL ES capability contracts.

### Legacy and modern devices

The registry includes x86/ARM/RISC-V and legacy architecture metadata, PCI/PCIe/USB/virtio/NVMe/SATA/SCSI/I2C/SPI/GPIO/Bluetooth classes, audio, camera, input, network, storage and display categories.

### Printers

The print subsystem prefers protocol-level support: IPP Everywhere/driverless printing, PostScript, PCL, ESC/P and virtual PDF/PS output. `ghost_printer.c` is a safe virtual sink for testing and deterministic output; it is not a physical-device driver.

## Licensing rule

Do not vendor proprietary Windows drivers. Do not copy Linux/Mesa/CUPS/SANE source into the repository without preserving the original license and attribution. New Chimera code is clean-room adapter code. External driver/provider components must remain optional and provenance-tracked.
