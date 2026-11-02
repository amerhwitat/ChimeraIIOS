# Installed-system GRUB 2 boot path

The installation media menu is not the installed-system bootloader. A completed disk installation must place Koronos and its selected production initramfs under the target root's `/boot`, install GRUB 2 to the selected boot device, and generate a target-local `/boot/grub/grub.cfg`.

## Explicit post-deployment operation

`installer/boot/install-grub2.sh TARGET_ROOT BOOT_DEVICE bios|uefi [EFI_DIRECTORY]`

- `TARGET_ROOT` is the mounted installed root filesystem.
- `BOOT_DEVICE` is the whole boot disk (for example `/dev/sda` or `/dev/nvme0n1`), not a partition.
- BIOS installs the i386-pc GRUB core to the selected disk.
- UEFI requires the mounted FAT EFI System Partition (default `TARGET_ROOT/boot/efi`) and installs the x86_64-efi GRUB loader with the ChimeraIIOS boot ID.
- The script refuses to proceed unless the target has the Chimera install marker, Koronos ELF, a block-device destination, a discoverable root UUID, and the required GRUB utilities.
- The generated menu searches the installed root by filesystem UUID, starts the installed Koronos ELF, passes the installed initramfs and optional manifest, and exposes Recovery. It never silently falls back to the installation ISO.

## Important integration boundary

This helper is an explicit bootloader-install operation, not yet an automatic final phase of `Installer::execute`. The current C++ InstallPlan has no selected boot-device, EFI System Partition, or firmware-confirmation fields, and its current execute path copies payloads but does not partition/mount disks. The installer UI/backend must collect and validate those selections, invoke this helper only after durable deployment and verification, and fail the transaction if GRUB installation or post-install boot-file checks fail. Do not report installation complete or reboot before that integration exists.

The installed menu's initramfs must be a production installed-system image, not a synthetic candidate or an ISO-only Live image. The current runtime acceptance blocker remains in force.
