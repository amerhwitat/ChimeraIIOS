# Chimera II Live CD

The boot chain is now **Chimera-native**:

**Firmware → Spit Fire → Jasper → Koronos → drivers/storage/network → Kore → Aurora or installer/recovery**

- **Koronos** is the executable Live-CD kernel and is loaded directly as a Multiboot2 ELF64 image.
- **Spit Fire** is the native BIOS/UEFI bootloader path.
- **Jasper** is the boot-manager/menu layer.
- **GRUB2** is the ISO/firmware compatibility loader and uses the same Koronos ELF.
- **Gates** exposes the same structural boot/install/recovery choices from Aurora.
- **Installation**, **Recovery**, and **Diagnostics** reuse the Koronos kernel and receive their payloads as Multiboot2 modules.
- A Linux `vmlinuz` is **not required** for the Chimera Live boot path.

The current Koronos kernel initializes the native kernel/runtime and records Multiboot2 payload modules. Desktop/userland execution remains a separate kernel-to-userland milestone; the boot media no longer substitutes a Linux kernel for Koronos.
