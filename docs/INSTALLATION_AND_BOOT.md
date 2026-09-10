# Chimera II OS Installation and Boot

Chimera II uses a layered boot architecture: Spit Fire is the native Chimera loader, GRUB2/Multiboot2 is the standards-based fallback, and compatibility entries can chainload Linux and Windows boot managers. LILO is supported as a legacy Linux compatibility target where its environment is appropriate.

The same installer plan is shared by ISO, Live DVD, USB, SSD, NVMe and HDD installation media. The graphical installer provides keyboard and mouse operation, disk discovery, GPT/MBR selection, guided/manual partitioning, filesystem selection, formatting, file-copy progress, bootloader installation, verification and reboot.

## Safety model

Disk writes are staged as an explicit plan. Deletion and formatting require confirmation after the exact disk/partition targets are shown. The installer records an operation journal and verifies the final boot configuration before offering reboot.

## Boot standards

GRUB2's Multiboot2 interface is used for the portable kernel/installer handoff. Multiboot2 defines the bootloader/OS interface and permits multiple bootloader implementations to load compliant images. citeturn0search0turn0search6

Modern GRUB supports Multiboot2 and modern Linux loading, making it the preferred standards-based fallback. citeturn0search8

LILO remains a compatibility/legacy path; it installs boot code and configuration for Linux systems but is not the primary modern UEFI path. citeturn0search3

## Windows media

Windows-targeted setup follows Microsoft's bootable-media model and separates the Windows-hosted launcher from the bootable installation environment. Microsoft's documentation covers both UEFI/legacy boot modes and Windows installation from bootable media. citeturn0search1turn0search5

The Chimera installer must not claim universal support for every historical Windows release when modern .NET dependencies are used; the native bootstrap remains separate for compatibility.
