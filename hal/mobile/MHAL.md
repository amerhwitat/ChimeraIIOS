# Chimera II Mobile Hardware Adaptation Layer (MHAL)

MHAL is the hardware boundary between Koronos Mobile Microkernel and model-specific mobile hardware.

## Layers

```text
Koronos Mobile Microkernel
        |
       MHAL
        |
  SoC / board adapter
        |
+-------+--------------------------------+
| CPU | GPU | display | touch | audio    |
| USB | storage | Wi-Fi | BT | modem     |
| GPS | sensors | camera | battery       |
+----------------------------------------+
```

## Design rules

- A CPU architecture match is not sufficient for device support.
- Every physical device requires a hardware profile before a bare-metal image is considered installable.
- Vendor firmware remains outside the core unless redistribution rights exist.
- Drivers use explicit capability and ABI boundaries.
- Secure Boot, AVB, signed firmware and hardware roots of trust are respected rather than bypassed.
- Recovery and rollback information is mandatory for experimental flashing.
- Hosted Android and iOS builds use the vendor OS APIs instead of requiring MHAL.

## Android

Android adapters may consume AOSP interfaces, Android HAL boundaries, GKI/KMI interfaces, vendor modules and device-tree/ACPI information when available.

## Apple mobile hardware

Apple mobile bare-metal support is a research/device-profile target only. Stock locked iPhone/iPad hardware cannot be represented as universally flashable. A target requires a technically and lawfully available boot path and sufficient hardware interfaces.

## Test levels

1. emulator
2. hosted application
3. development board
4. boot-chain validation
5. display/input validation
6. storage/network validation
7. power-management validation
8. complete device qualification

No image is promoted to a general mobile release solely from emulator success.
