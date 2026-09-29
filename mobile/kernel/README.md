# Chimera II Mobile Kernel Integration

The mobile edition shares the Koronos microkernel ABI with the desktop/server edition while keeping device-specific boot code outside the common payload.

## Architecture

```text
Device firmware / vendor boot chain
        |
        +-- Android fastboot/recovery adaptation
        +-- Apple signed deployment path
        +-- other vendor-specific boot adapter
        |
        v
Device-specific Koronos boot bundle
        |
        v
Koronos microkernel
  +-- capability handles
  +-- endpoint IPC
  +-- scheduler/synchronization/timers
  +-- N-bit execution policy
  +-- hardware/firmware discovery
        |
        +-- mobile HAL / drivers
        +-- Android hosted compatibility layer
        +-- Aurora mobile shell
```

The desktop `x86_64` Koronos ELF is **not** flashed directly to an ARM phone. Mobile builds first select an architecture/device profile and then require a device-specific signed boot/adaptation bundle.

## Current build boundary

`mobile/build-mobile-edition.sh` produces the mobile edition manifest and a reference copy of the host Koronos ELF for ABI/build tracking. It intentionally does not manufacture a phone boot image from an x86_64 ELF.

## Flash safety

`mobile/flash/mobile-flash-tool.sh` supports device discovery, payload preparation, manifest validation and dry-run verification. Any future write adapter must use an exact device manifest, verified image hashes, signed images, explicit rollback policy and an explicit user confirmation. Generic partition flashing and authentication/unlock bypasses are not part of the Chimera flash contract.

## Android

The supported integration transports are ADB/fastboot/recovery when a device profile explicitly defines them. Android vendor kernels, DTBs, firmware and bootloaders remain device-specific adaptation inputs.

## Apple

Apple deployment remains hosted/signed through the Apple toolchain. The common mobile runtime does not attempt to replace Apple's signed boot chain.
