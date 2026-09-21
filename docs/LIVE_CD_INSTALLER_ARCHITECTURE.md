# Chimera II Live CD and Installer pipeline

## Boot

1. Firmware selects Spit Fire.
2. Spit Fire loads Jasper and exposes BIOS/UEFI boot options.
3. Jasper selects Live, Install, Safe Graphics, Diagnostics, Recovery or Network.
4. The native path enters Koronos through the Live entry contract.
5. Koronos starts hardware/storage/network/graphics services.
6. Kore starts Aurora or the text installer.
7. The installer consumes the Live payload and creates a transaction plan.
8. After explicit confirmation, the selected storage/filesystem/bootloader backend deploys the system.
9. Verification checks the installed payload and boot configuration before reboot.

## Installer modes

- Aurora Wayland Glass GUI: central installation summary with asynchronous hardware/storage detection.
- CLI text: keyboard-only workflow using the same installer core.
- Live: no disk mutation.
- Recovery: verification and repair services.
- Compatibility: POSIX/Linux, BSD, Windows and Darwin user-space adapters.

## Media

The builder can start from an existing chimera-ii-os.iso, a release asset, or create a fresh GRUB2/Multiboot2 ISO. Spit Fire IMG artifacts are staged beside Koronos. Existing boot information is preserved when xorriso performs an in-place ISO edit.

## Library artwork

The installer GUI background is sourced from the Library asset Aurora Wayland Glass Desktop.png. A materialized copy can be passed with CHIMERA_AURORA_BACKGROUND; the binary is not duplicated into Git source control.

## Build

Linux/WSL:
  tools/build-full-iso.sh

Windows:
  tools/build-full-iso.bat
  tools/build-full-iso.ps1

To fetch release media automatically:
  CHIMERA_FETCH_RELEASE=1 CHIMERA_RELEASE_TAG=latest tools/build-full-iso.sh

The build compiles the CMake graph plus the freestanding koronos-x86_64 target, stages installer/Aurora/Kore/userland/boot payloads, edits a base ISO when available, hashes the result, and publishes build artifacts in CI.
