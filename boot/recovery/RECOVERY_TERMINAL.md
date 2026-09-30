# Chimera II OS Repair Terminal

The Jasper boot menu now exposes **Repair Terminal / Recovery**. It loads Koronos together with a dedicated recovery initramfs and opens the Chimera recovery console before the installed root filesystem is required.

## Commands

- `help` — command reference
- `status` — kernel, recovery and mount state
- `disks` — block devices/filesystem identifiers
- `mounts` — current mounts
- `logs` — early boot and initramfs logs
- `dmesg` — kernel messages
- `drivers` — Chimera driver inventory
- `network` — interfaces and routes
- `mount-root [device] [rw|ro]` — mount an installed root filesystem at `/mnt/chimera-root`
- `umount-root` — unmount the installed root
- `check-root [device]` — non-destructive filesystem check (`fsck -fn`)
- `repair-root [device]` — filesystem repair after explicit `REPAIR` confirmation
- `verify` — verify required Koronos/Jasper/Live files on the mounted root
- `rollback` — inspect Chimera rollback/checkpoint directories
- `boot-normal` — bind early filesystems and attempt `switch_root` to the installed system
- `shell` — underlying BusyBox shell
- `reboot` / `poweroff` — restart or power off
- `exit` — leave the command loop

The repair console follows the same early-userspace recovery model used by established Linux initramfs environments: a boot failure can deliberately stop in an interactive shell so devices, mounts and logs can be inspected before attempting the normal root transition. citeturn0search0turn0search8

## Build artifacts

The build produces:

```text
build/live-boot/boot/recovery/chimera-recovery-initramfs.img
build/live-boot/boot/recovery/chimera-recovery-initramfs.img.sha256
build/live-boot/boot/recovery/recovery-manifest.json
```

The ISO builder stages those files at:

```text
/boot/recovery/chimera-recovery-initramfs.img
/boot/recovery/recovery-manifest.json
/boot/jasper/recovery.cfg
```
