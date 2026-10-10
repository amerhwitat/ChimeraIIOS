# Chimera II OS Mobile Edition

Chimera II Mobile is the mobile delivery layer for Chimera II OS. It shares the canonical Koronos, RegisterN, security, networking, database, toolchain, package and application contracts with the desktop and bare-metal editions while respecting Android and Apple platform security boundaries.

## Editions
- Android: hosted APK/AAB runtime plus device-profiled recovery integration.
- iOS/iPadOS: hosted application/runtime integration using Apple-supported APIs and signing.
- Common mobile core: versioned manifests, capability negotiation, updates, diagnostics and recovery contracts.

## Boot pipeline

`UEFI/vendor boot ROM -> Spit Fire/Jasper -> verified artifacts -> Koronos -> mobile initramfs -> hardware probe -> display/input/audio/network/power services -> Aurora Mobile shell`

The mobile boot path must expose visible progress states for firmware, verification, kernel bring-up, hardware discovery and shell startup. Recovery remains independently bootable.

## Synchronization
mobile/mobile-sync.json maps desktop/ISO components to mobile equivalents. The mobile build consumes the same source tree and registries rather than maintaining a divergent implementation.

## Native toolchain
The mobile SDK exposes chimera-cc, chimera-cxx, chimera-gas and chimera-ld. Android selects the Android NDK/Clang toolchain; Apple targets select Apple Clang/Xcode on macOS.

## Hardware contracts

The production mobile HAL set is expected to cover ARM64 SoC discovery, DRM/KMS or platform display composition, touch and sensors, audio, Wi-Fi, Bluetooth, modem/SIM/eSIM, USB-C/PD, camera, battery/fuel gauge, thermal management and suspend/resume.

## Updates and recovery

Use A/B-style update slots where the device architecture permits it. The updated slot must be marked successful only after a verified successful boot; failed updates return to the previous known-good slot. Recovery and rollback metadata must be authenticated.

## Aurora Mobile

The touch-first shell should share the Aurora visual language and artwork catalog with the desktop edition while adding a launcher, notification shade, quick settings, lock screen, gesture navigation, safe-area handling and dynamic scaling.

## Security
Mobile flashing is confirmation-gated and device-profile constrained. The tooling does not bypass bootloader locks, Android Verified Boot, Apple secure boot, signing, recovery protections or vendor security controls.

## Status

The common contracts and roadmap are present; production device support remains profile-specific and requires hardware validation before a device is declared supported.

## Endianness and cross-architecture boundaries

Mobile builds consume the shared [endianness contract](../system/architecture/endianness.json) and freestanding helpers at `kernel/include/chimera/endianness.h`. The device OS/SoC ABI determines native data order; the boot handoff records the target and active mode. Microkernel IPC uses canonical little-endian serialized fields, while native in-memory structures remain ABI-specific. Android/iOS hosted execution does not establish that an emulated guest shares the host byte order. Emulators and compatibility layers must keep guest byte order independent and validate executable format metadata. Device-specific kernel, driver, Aurora and endian-mode behavior is not considered validated until tested on the named target profile.

The x86-32 Koronos probe is shared as a development target only; it does not imply a complete 32-bit mobile kernel or device boot image. See [the 32-bit bring-up plan](../docs/koronos-32bit-bringup.md).
