# Chimera II OS Mobile Edition

Chimera II Mobile is the mobile delivery layer for Chimera II OS. It shares the canonical Koronos, RegisterN, security, networking, database, toolchain, package and application contracts with the desktop and bare-metal editions while respecting Android and Apple platform security boundaries.

## Editions
- Android: hosted APK/AAB runtime plus device-profiled recovery integration.
- iOS/iPadOS: hosted application/runtime integration using Apple-supported APIs and signing.
- Common mobile core: versioned manifests, capability negotiation, updates, diagnostics and recovery contracts.

## Synchronization
mobile/mobile-sync.json maps desktop/ISO components to mobile equivalents. The mobile build consumes the same source tree and registries rather than maintaining a divergent implementation.

## Native toolchain
The mobile SDK exposes chimera-cc, chimera-cxx, chimera-gas and chimera-ld. Android selects the Android NDK/Clang toolchain; Apple targets select Apple Clang/Xcode on macOS.

## Security
Mobile flashing is confirmation-gated and device-profile constrained. The tooling does not bypass bootloader locks, Android Verified Boot, Apple secure boot, signing, recovery protections or vendor security controls.
