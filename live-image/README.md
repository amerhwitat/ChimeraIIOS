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

GRUB menu: Live desktop, Classic X session (openbox + xterm), Safe graphics
(`nomodeset`), Verbose boot, Reboot, Power off.

Console access: `Ctrl+Alt+F2`, user `live`, password `live`, passwordless `sudo`.

## Requirements (build host)

`debootstrap xorriso squashfs-tools grub-pc-bin grub-efi-amd64-bin mtools dosfstools imagemagick python3`

Run as root (the script re-executes itself with `sudo` if needed).

## Honest scope

This image packages the project's **userland** (HTML desktop, catalogs, artwork, source
snapshot) on a Linux kernel. It does not boot the project's native Spit Fire/Koronos
microkernel: upstream documentation records that the kernel does not yet reach a
verified userspace handoff, so release of a native-kernel ISO remains blocked. Nothing
here claims otherwise — the boot menu, session and artwork are real, the microkernel is
not in the boot path.

## Environment knobs

| Variable | Meaning |
| --- | --- |
| `BUILD_ROOT` | build directory (default `live-image/.build`) |
| `OUT_DIR` | ISO output directory (default `$BUILD_ROOT/out`) |
| `JOBS` | squashfs/xz parallelism |
| `REBUILD_BASE=1` | recreate the base rootfs from scratch |
