# Chimera II OS 2026.11.02 (fullscreen desktop fix) — live ISO chimera-ii-os-live-2026.11.02-desktop-64ca6a598f13

Rebuild of the 2026.11.02 live image on top of `64ca6a598f13` with the desktop
fullscreen fix: the Aurora kiosk now fills the screen under Openbox at 1280x720 and
1920x1080 (verified), instead of rendering at its intrinsic size.

Source tree also carries the 26 attached wallpapers introduced in 960c5c1 and the offline application catalogs staged in 64ca6a5.

| Field | Value |
| --- | --- |
| File | `chimera-ii-os-live-amd64.iso` |
| Size | 486,725,632 bytes (464 MiB) |
| SHA-256 | `c37615113953348cbf9c18bfd1fc021db838b37b09be7abdd673b491d07b5bfc` |
| Volume label | `CHIMERA_II_OS` |
| Kernel | Debian `6.12.107+deb13-amd64` |
| Firmware | BIOS (El Torito) + UEFI (`efi.img`), GRUB 2.12 |
| Source commit | `64ca6a598f13` |

## Download

- ISO — https://github.com/amerhwitat/ChimeraIIOS/releases/download/chimera-ii-os-live-2026.11.02-desktop-64ca6a598f13/chimera-ii-os-live-amd64.iso
- Release page — https://github.com/amerhwitat/ChimeraIIOS/releases/tag/chimera-ii-os-live-2026.11.02-desktop-64ca6a598f13
- Download index (both editions, checksums, wallpapers) — https://amerhwitat.github.io/downloads/#live-isos
- Superseded build — https://github.com/amerhwitat/ChimeraIIOS/releases/tag/chimera-ii-os-2026.11.02

## Contents

- `/opt/aurora/desktop` — the project's HTML desktop, patched at build time, now launched fullscreen.
- `/opt/aurora/wallpapers` — 26 offline wallpapers (2560 px JPEG), mirrored to `/usr/share/backgrounds/`.
- `/opt/aurora/repo` — verbatim source snapshot at the build commit, including the offline app catalogs.
- `/opt/aurora/PROJECT.md` — provenance record written by the build.

## Boot

GRUB entries: "Live desktop" (Aurora kiosk), "Classic X session (openbox)", "Safe graphics (nomodeset)",
"Verbose boot". Live login `live` / `live`, root `live`, passwordless sudo. BIOS and UEFI both supported;
the attached `ISO-BOOT-REPORT.txt` is the El Torito/GPT/APM map read back from the published image.

## Scope

The image runs the Debian Linux kernel with this repository's Aurora desktop and userspace payload. It is
not a build of the native Spit Fire/Koronos kernel and does not discharge the native userspace-handoff
acceptance gates tracked in `docs/`. Third-party catalog entries are not installed or certified
applications unless stated.

## Verification (2026-11-03)

- Published `.sha256` asset matches the released file byte for byte (`c37615113953348c…`), size 486,725,632 bytes.
- Both download URLs return the ISO directly (HTTP 302 → 200, correct `content-length`).
- Boot report confirms BIOS `eltorito.img` plus UEFI `efi.img` hybrid layout with GPT/APM entries.
