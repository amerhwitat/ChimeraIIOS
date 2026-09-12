# Chimera II Hardware / Driver Compatibility Layer

This directory is a **capability registry, driver adapter boundary, and secure acquisition layer**. It is not a redistribution channel for proprietary Windows or vendor driver binaries.

## Coverage model

- CPU/SoC: x86, ARM, RISC-V plus legacy MIPS/PowerPC/SPARC metadata.
- GPU: NVIDIA, AMD, Intel, Apple, ARM Mali, Qualcomm Adreno, Imagination PowerVR, 3dfx, Matrox, S3, VIA, SiS and virtual GPUs.
- buses/classes: PCI/PCIe, USB, NVMe/SATA/SCSI, virtio, I2C/SPI/GPIO, networking, audio, camera, input and display.
- graphics APIs: OpenGL/OpenGL ES, Vulkan and optional vendor/compute adapters.
- audio: ALSA/PipeWire/PulseAudio compatibility, WASAPI and CoreAudio adapter boundaries.
- printing: IPP Everywhere, PostScript, PCL, ESC/P, PDF/PS and virtual/ghost output.

## Driver acquisition

`python/driver_acquisition.py` and the native C ABI implement a secure **discover → match → acquire → verify → stage → explicitly install** model.

The acquisition broker:

- restricts sources to curated HTTPS allowlists;
- validates hardware IDs before staging;
- verifies SHA-256 digests;
- checks signature/trust metadata;
- records SPDX/license and provenance information;
- keeps downloaded artifacts inert in quarantine/staging;
- never silently loads a kernel module;
- never disables Secure Boot or driver-signature enforcement.

### Linux

Linux kernel modules are kernel-ABI-specific. Chimera therefore accepts a Linux `.ko` candidate only when the declared ABI matches the Koronos policy. Otherwise it acquires source/package metadata for a Chimera-specific port or adapter. This avoids pretending that an arbitrary Linux binary module is compatible with the Chimera kernel.

### Windows

Windows INF/CAT/SYS packages are verified and staged as candidates. On Windows, final installation is delegated to the native Driver Store/SetupAPI path and its signature policy rather than bypassing platform security.

### Source policy

Curated acquisition sources live in `acquisition_sources.json`. The source updater manages metadata; it does not execute downloaded drivers. Open-source source is integrated only with its original compatible license and provenance retained.

See `docs/DRIVER_ACQUISITION.md` for the complete flow.
