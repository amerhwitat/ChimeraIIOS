# Chimera II OS — Spit Fire to Aurora Boot Sequence

## Canonical sequence

1. BIOS or UEFI firmware selects the Chimera boot entry.
2. Spit Fire initializes the architecture-specific bootstrap path.
3. Spit Fire/UEFI constructs the normalized boot context and preserves firmware, memory-map, framebuffer, ACPI/SMBIOS and boot-media information.
4. Jasper/Gates presents the Aurora menu using the canonical artwork.
5. The selected path enters Koronos through Multiboot2/CHMBOOT1.
6. Koronos validates the handoff before touching the boot-information region.
7. Koronos detects CPU/native execution width and selects the configured Chimera N-bit execution mode.
8. Koronos discovers motherboard/platform, storage, network and display/GPU hardware.
9. The driver manager binds native drivers first and verified compatibility adapters second.
10. Kore/Nucleus/Hive/Aegis/Spotnik services become available.
11. The Aurora visual runtime starts.
12. The same Aurora background is selected for Live, Installer, Recovery, Diagnostics and the installed Desktop.

## Live CD

`Jasper -> /boot/jasper/live.cfg -> /boot/koronos/koronos.elf -> /boot/live/chimera-live-initramfs.img -> Aurora Live`

The Live manifest is `/boot/live/live-manifest.json`.

## Installer

`Jasper -> /boot/jasper/install.cfg -> /boot/koronos/koronos.elf -> installation payload -> Aurora Installer`

The installer manifest is `/installer/installer-manifest.json` in the source tree and is staged with the installation media by the ISO build.

## Installed Desktop

After installation the Aurora session prefers:

`/usr/share/chimera/aurora/ChimeraIIOS-Aurora-Wayland-Glass.jpg`

and falls back to `/boot/visual/aurora-wayland-glass.jpg`, then to the repository SVG only if neither installed raster asset is available.

## Artwork materialization

The user-supplied Aurora image is embedded at:

`boot/visual/aurora-wayland-glass.jpg.b64`

The build entrypoint `build-chimera-iso-aurora.sh` materializes it into the build tree and invokes the existing comprehensive ISO builder with `--background`.

The artwork is validated before the ISO builder starts. This prevents an ISO from being declared visually complete when the canonical background is missing or corrupted.

## Failure boundaries

A failure in the visual layer must not prevent recovery. Koronos, Safe Graphics, Diagnostics and Recovery remain usable without a Wayland compositor. The artwork is therefore mandatory for the normal GUI paths but non-fatal to kernel/recovery execution.
