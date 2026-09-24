# VMware support

Chimera II OS uses UEFI/EFI firmware, a virtual disk, vmxnet3 networking, xHCI USB, and SVGA graphics in the generated VMX. This is suitable for VMware Workstation/Fusion and can be imported into VMware environments; exact hardware-version/device availability depends on the VMware product and host.

The current native boot contract is Koronos ELF via the ISO bootloader chain. Legacy GRUB entries that reference /vmlinuz or /initrd.img are not used.
