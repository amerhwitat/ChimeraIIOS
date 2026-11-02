# Live image builder

Builds a bootable, hybrid BIOS/UEFI x86_64 live ISO for this project: a Debian-based
live system whose session renders the project's own HTML desktop fullscreen (WebKit2GTK
kiosk) with the supplied artwork wired into every page's background picker.

```sh
sudo ./live-image/build.sh chimera      # -> live-image/.build/out/chimera-ii-os-live-amd64.iso
```

The script bootstraps its own base rootfs with `debootstrap`, so no Docker or
cross-toolchain is required.

## What ends up in the image

| Path | Contents |
| --- | --- |
| `/opt/aurora/desktop` | the repository's HTML desktop, patched with the wallpaper overlay |
| `/opt/aurora/wallpapers` | shipped artwork (`index.json` is the manifest) |
| `/opt/aurora/repo` | verbatim source snapshot (provenance) |
| `/usr/share/backgrounds/<edition>` | the same artwork for the openbox session |
| `/usr/local/bin/aurora-kiosk.py` | fullscreen WebKit2GTK shell |
| `/usr/local/bin/aurora-session` | session entry point (kiosk or `session=classic`) |

GRUB 2, Jasper and Spit Fire share `/boot/jasper/live-image.cfg` and expose:

- **Live — Aurora Desktop** (default Linux-kernel live edition).
- **Installer — Native Koronos Installer** (visible, but fail-closed unless the native kernel, installer initramfs, installation image, and all contracts are staged).
- **Koronos — Native Kernel Diagnostics** (experimental ELF target; not a production userspace release).
- **Recovery — Linux Rescue Shell** (boots the Linux live kernel into a console shell with filesystem, partition, network and diagnostic tools).
- **Recovery — Native Koronos Recovery** (fail-closed until its dedicated initramfs and manifest are staged).
- Classic X, Safe graphics, Jasper, Spit Fire and GRUB diagnostics.

The menu requests `5120x2880` first, then supported 4K/HD/SVGA fallbacks through `640x480`, and keeps `gfxpayload=keep`. The selected mode is limited by what the firmware/virtual GPU advertises. GRUB debug, kernel `loglevel=7 ignore_loglevel printk.time=1 initcall_debug`, and systemd debug/status-to-console are enabled by default.

Console access: `Ctrl+Alt+F2`, user `live`, password `live`, passwordless `sudo`.

## Requirements (build host)

`debootstrap xorriso squashfs-tools grub-pc-bin grub-efi-amd64-bin mtools dosfstools imagemagick python3`

Run as root (the script re-executes itself with `sudo` if needed).

## Honest scope

The default Live desktop and Linux Rescue Shell boot the Debian-based live system.
The ISO build also compiles and bundles the native Koronos ELF as an experimental
diagnostic menu target; that does not prove successful native userspace handoff and
does not make this a native Koronos production release.

Native Installer and native Koronos Recovery are exposed in the unified menu but
remain fail-closed until their complete production initramfs/image payloads are
available. The Linux Rescue Shell is not represented as native Koronos Recovery.
Physical-machine boot acceptance is separate from the QEMU CI tests.

## Environment knobs

| Variable | Meaning |
| --- | --- |
| `BUILD_ROOT` | build directory (default `live-image/.build`) |
| `OUT_DIR` | ISO output directory (default `$BUILD_ROOT/out`) |
| `JOBS` | squashfs/xz parallelism |
| `REBUILD_BASE=1` | recreate the base rootfs from scratch |
| `KORONOS_ELF` | optional native ELF to stage (default build output path) |
| `INSTALLER_INITRAMFS` | native installer initramfs; required for the Installer target |
| `INSTALLATION_IMAGE` | native installer image; required for the Installer target |
| `RECOVERY_INITRAMFS` | native recovery initramfs; required for native Koronos Recovery |
