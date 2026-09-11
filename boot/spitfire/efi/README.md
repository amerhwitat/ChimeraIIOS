# Spit Fire UEFI loader

The UEFI source uses gnu-efi when that toolchain is installed. The ISO builder does not require it: environments without an EFI cross-toolchain retain the GRUB/xorriso UEFI path when available and otherwise use the existing Multiboot2 BIOS bootstrap.

Expected installed path in the final media: `EFI/BOOT/BOOTX64.EFI`. The loader boundary records the firmware/system-table contract and reserves the kernel verification and `ExitBootServices` handoff for the production EFI build.
