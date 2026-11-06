# Chimera II OS live ISO 2026.11.06 (28-wallpaper desktop build)

- Release: [chimera-ii-os-live-2026.11.06-desktop-6182685](https://github.com/amerhwitat/ChimeraIIOS/releases/tag/chimera-ii-os-live-2026.11.06-desktop-6182685)
- Source commit: `6182685`
- Image: `chimera-ii-os-live-amd64.iso`
- Size: 491,644,928 bytes (469 MiB)
- SHA-256: `b5eefa6f959643f5f2321ea994dc8e576723f5339fa08abd8093bb128abb88c1`
- Boot targets: BIOS (El Torito) and UEFI (`/efi.img`), serial console on every entry
- GRUB: `set timeout=300` with `set timeout_style=menu` — Jasper, Gates, Aurora, Classic X,
  Safe graphics and Verbose entries wait for an explicit choice
- Wallpapers: 28 (wp01-wp28), including the two supplied desktop reference images
- Desktop: Aurora shell (Jasper/Windows 12, Gates/macOS, Aurora/Linux 7.x profiles) with
  VoiceConnect and the Network Applications panel

## Verification for this build

- `live-image/build.sh` completed the full pipeline (payload staging, SDK report, squashfs, ISO).
- `/boot/grub/grub.cfg` extracted from the image shows the 300 s menu and all profile entries.
- Release asset re-downloaded over HTTPS: HTTP 200, size matches the uploaded object.

Scope: the image boots a Debian Linux kernel with the project's own userland and desktop. It is
not a native Koronos release; the native ring-3 gate is tracked separately in
`docs/PRODUCTION_USERSPACE_HANDOFF.md`.
