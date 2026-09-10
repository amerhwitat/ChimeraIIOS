# Chimera II OS Boot and Installation Architecture

## Boot menu

The installation media provides one unified menu:

1. **Spit Fire native Chimera II** — native BIOS/UEFI path for Koronos.
2. **GRUB2 / Multiboot2** — standards-based path for Chimera II and Linux.
3. **LILO compatibility** — legacy Linux boot configuration/chainload entry where firmware and media support it.
4. **Linux** — discover and chainload installed Linux entries.
5. **Windows Boot Manager** — UEFI chainload of `\\EFI\\Microsoft\\Boot\\bootmgfw.efi` when present.
6. **Chimera II Setup** — graphical installer.
7. **Hardware diagnostics / recovery**.

GRUB2 is used as the standards-oriented fallback because it supports Multiboot2 and modern Linux loading. LILO is retained as a compatibility/legacy entry rather than being required for modern UEFI systems.

## Media targets

The build system produces:

- BIOS/UEFI bootable ISO/DVD
- UEFI-capable USB installation media
- Live environment image
- Windows-hosted installer package
- Linux-hosted installer package
- disk installation payload for SSD/NVMe/HDD

## Installation flow

1. Boot media.
2. Select `Chimera II Setup`.
3. Detect firmware, CPU, memory, disks and existing operating systems.
4. Choose language, keyboard and accessibility options.
5. Choose target disk.
6. Select automatic, guided, or manual partitioning.
7. Review destructive operations.
8. Create/delete/resize partitions where supported by the selected backend.
9. Select a supported Chimera filesystem.
10. Create ESP/boot partition as required by firmware mode.
11. Format selected filesystems.
12. Copy kernel, initramfs, system files, bootloaders and configuration.
13. Install Spit Fire and register the selected boot menu entries.
14. Install/configure GRUB2 fallback and Linux/Windows chainload entries where applicable.
15. Configure services, hostname, users and networking.
16. Verify installed files and boot configuration.
17. Show final progress/result screen.
18. Offer `Reboot`, `Return to Live Environment`, or `Shutdown`.

All destructive disk operations require an explicit final confirmation and identify the selected disk and partitions before execution.

## GUI

The installer UI is designed for mouse and keyboard operation and exposes every operation through a backend abstraction so the same workflow can be hosted by Aurora/Qt, Windows/.NET, JavaFX, or the live installer frontend.
