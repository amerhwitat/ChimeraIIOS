# Chimera II OS Boot and Installation Architecture

## Universal boot contract

Chimera II separates firmware/bootloader concerns from the Koronos kernel through `boot/boot_protocol.json`. The kernel accepts a normalized `CHMBOOT1` boot context instead of depending on one vendor bootloader.

Supported computer entry paths: native Spit Fire, BIOS/MBR, UEFI EFI application, Multiboot1/2, Limine-compatible handoff, and foreign/native bootloader chainload.

Legacy BIOS normally begins at 0x7C00 in 16-bit real mode; the x86 path therefore has explicit real16, protected32 and long64 transition boundaries. Other ISAs use their own architectural privilege states rather than being mislabeled real/protected mode.

## Boot menu first, GUI second

Jasper/Spit Fire presents a selectable menu, then transfers to the Aurora boot UI after a valid kernel/boot context has been selected. `boot/startup/boot_phase_manifest.json` defines the progress phases and visible component/application list.

The startup artwork is the embedded Aurora Wayland Glass visual in `boot/splash/aurora_boot_splash.svg`, designed at 3840x2160 and represented in the freestanding boot layer by `boot/splash/aurora_boot_ui.h`. The visible startup phases cover firmware/CPU mode, bootloader, menu, hardware discovery, memory, framebuffer, Koronos, drivers/MHAL, Spotnik, Nucleus/Hive/Kore/Aegis, Aurora compositor and user session.

## CPU modes

`boot/mode_matrix.json` records the architectural states. x86/x86-64 support real16, protected32, long64, compatibility and virtual-8086 environments. AArch64 uses EL0-EL3; RISC-V uses M/S/U; other architectures retain their native privilege models.

## Media targets

The build system is designed for BIOS/MBR, UEFI, hybrid ISO/USB, hosted Windows/Linux, Android/iOS hosted applications, and profile-specific bare-metal images. Hardware installation requires a validated profile, signed-image checks where applicable, explicit target selection and recovery/rollback planning.

## Build automation

- `tools/build/build-hosted.bat` / `.ps1` / `.sh` — hosted edition
- `tools/build/build-msi.ps1` — WiX MSI packaging
- `tools/build/build-mobile.sh` — Android/iOS hosted orchestration
- `tools/build/build-baremetal.sh` / `.ps1` — bare-metal orchestration
- `tools/build/build-all.sh` — aggregate Linux orchestration

An MSI requires WiX; Apple hosted builds require macOS/Xcode and signing credentials as applicable.

## Safety

Secure Boot, AVB, Apple secure boot and vendor boot protections are respected. Chimera does not claim that an arbitrary locked device can be flashed. Bootloader adapters may chainload a foreign/native loader without bypassing firmware security.
