# Chimera II Hardware / Driver Compatibility Layer

This directory is a **capability registry and adapter boundary**, not a redistribution of proprietary Windows or vendor driver binaries.

## Coverage model

- CPU/SoC: x86, ARM, RISC-V plus legacy MIPS/PowerPC/SPARC metadata.
- GPU: NVIDIA, AMD, Intel, Apple, ARM Mali, Qualcomm Adreno, Imagination PowerVR, 3dfx, Matrox, S3, VIA, SiS and virtual GPUs.
- buses/classes: PCI/PCIe, USB, NVMe/SATA/SCSI, virtio, I2C/SPI/GPIO, networking, audio, camera, input and display.
- graphics APIs: OpenGL/OpenGL ES, Vulkan and optional vendor/compute adapters.
- audio: ALSA/PipeWire/PulseAudio compatibility, WASAPI and CoreAudio adapter boundaries.
- printing: IPP Everywhere, PostScript, PCL, ESC/P, PDF/PS and virtual/ghost output.

### Driver rule

Kernel drivers remain OS-specific. Chimera II exposes stable user/kernel capability contracts and adapters rather than copying Linux kernel or Windows WDK source. Existing open-source drivers may be integrated only under their original compatible license and with provenance retained.

The registry can be generated from PCI/USB hardware data sources and extended without changing the ABI.
