# Mobile Boot Architecture

The Mobile Microkernel accepts a normalized boot-information structure from platform firmware/boot code.

```text
ROM / Boot Firmware
        |
 verified image + measurements
        |
 Mobile boot adapter
        |
 BootInfo + memory map + CPU topology
        |
 Mobile Microkernel
        |
 capability-controlled system services
```

The boot layer must not assume that desktop BIOS/MBR/GRUB mechanisms exist on a phone or tablet. Platform adapters may consume UEFI, device-tree, firmware handoff or vendor boot metadata. Verified boot and rollback protection are mandatory design interfaces, while their concrete implementation belongs to the target platform.

## Shared Chimera II boot and artwork contract

The mobile edition shares the repository-level static contract in `boot/boot-menu-contract.json` and the canonical artwork/progress manifest in `boot/boot-artwork-manifest.json`. The desktop/ISO path describes Spit Fire → Jasper/GRUB menu handoff → Koronos → Aurora; mobile boot ROM/UEFI and ARM64/RISC-V trap entry remain platform-specific and must not be assumed to run x86 GRUB menu files directly.

The host-side checker `tools/boot/validate_boot_pipeline.py` verifies manifest consistency and artwork provenance only. Mobile release acceptance still requires target-specific bootloader, signature, device-tree/ACPI, exception-vector, initramfs, and hardware boot tests.
