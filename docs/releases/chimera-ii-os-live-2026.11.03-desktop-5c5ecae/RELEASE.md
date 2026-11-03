# Chimera II OS Live ISO 2026.11.03 (26-wallpaper build)

- Release: [chimera-ii-os-live-2026.11.03-desktop-5c5ecae](https://github.com/amerhwitat/ChimeraIIOS/releases/tag/chimera-ii-os-live-2026.11.03-desktop-5c5ecae)
- Source commit: `5c5ecae099011bc743adcc3cb00b1711cf56dccb`
- Image: `chimera-ii-os-live-amd64.iso`
- Size: 489,723,904 bytes (467 MiB)
- SHA-256: `5fec26dd53a3c90b124ca58437fd6552ebb4263b8bdeb865b01ad14d8a4e5a70`
- Boot targets: BIOS (El Torito, grub2-mbr) and UEFI (`/efi.img`)
- Wallpapers: 26 (wp01–wp26), applied as the default background and exposed in the desktop picker
- Desktop: `desktop/index.html` (Chimera `web/`) rendered fullscreen by the Aurora kiosk under Openbox
- Boot verification (this build): QEMU x86_64, 2 vCPU, 1600 MiB, `-cdrom`, serial capture
  reached multi-user and a `chimera-ii login:` prompt on `ttyS0`; the login banner reports
  commit `5c5ecae`.

Serial evidence (abridged):

```
  Chimera II OS 2026.11.03  ·  live image (x86_64)
  https://github.com/amerhwitat/ChimeraIIOS @ 5c5ecae

chimera-ii login:
```

Scope note: the image boots a Debian Linux kernel with the Chimera userland and desktop. It is
not a native Koronos release and does not satisfy the native userspace handoff gate
(`docs/PRODUCTION_USERSPACE_HANDOFF.md` is the OctavianOS contract for that path); the Koronos
preview in the gallery is a browser concept, not a kernel boot.
