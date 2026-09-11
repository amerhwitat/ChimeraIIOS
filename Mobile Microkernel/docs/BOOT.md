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
