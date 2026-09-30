# Chimera II OS Recovery Runtime Levels and Targets

## Runtime levels
- L0 Firmware / Pre-OS: BIOS/UEFI discovery and EFI System Partition access.
- L1 Koronos: dedicated Jasper/Koronos recovery initramfs with BusyBox utilities and conservative filesystem operations.
- L2 Linux: offline Linux installation recovery.
- L2 Windows: offline Windows installation recovery; NTFS/VFAT/exFAT support, with BitLocker detection but no encryption bypass.
- L2 macOS / OS X: offline macOS/OS X target discovery; HFS+/HFS and APFS detection. APFS read/write is only enabled when a verified compatible implementation is present.
- L3 Hosted: recovery tooling can be invoked from Linux, Windows, or macOS host environments without claiming native kernel control over the host.

## Filesystem mounting contract
Recovery defaults to read-only. The mount-target command selects a target OS and discovers candidate volumes. The mount-fs command performs an explicit filesystem mount.

## Targets
- Linux: ext4, XFS, Btrfs, ZFS, VFAT, exFAT, NTFS3, LUKS2/LVM/mdraid.
- Windows: NTFS3, VFAT, exFAT, EFI; BitLocker is detected but not decrypted by recovery.
- macOS/OS X: APFS/HFS+/HFS/VFAT/exFAT; APFS is detection-first unless an available implementation supports the requested mount mode.
- Chimera: QFS plus the supported Linux filesystems and ISO9660/UDF/SquashFS formats.

## Safety
Filesystem checks are non-destructive by default. Repair commands require explicit confirmation and an unmounted target. Platform security, encryption, Secure Boot, Apple security, and Windows protection mechanisms are not bypassed.
