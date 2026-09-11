# Structured ISO build

`build-iso.sh` creates a deterministic staging tree before ISO mastering.

## Media tree

- `boot/spitfire/` — SF0/SF1/SF2 source and boot ABI references.
- `boot/jasper/` — boot-manager configuration.
- `boot/koronos/` — bootstrap kernel payload and ABI metadata.
- `EFI/BOOT/` — standard UEFI fallback location produced by the GRUB/xorriso authoring path when available.
- `EFI/CHIMERA/` — Spit Fire UEFI source and future signed EFI payload.
- `chimera/` — application, mobile, toolchain, documentation and knowledge metadata.
- `src/` — reserved source payload area for complete source-enabled distributions.
- `checksums/` — SHA-256 manifest and JSON provenance metadata.

The existing Multiboot2 bootstrap remains the executable kernel path. The new Spit Fire stages are included as low-level implementation artifacts and can be selected by future native boot builds. The ISO builder does not silently turn research-only source into a claimed production kernel.

## Authoring

GRUB2 `grub-mkrescue` is preferred because it can construct the El Torito boot catalog and the BIOS/UEFI media layout. The build fails explicitly when no compatible ISO authoring backend is installed.

The ISO is an ISO 9660 filesystem image. A raw partitioned disk image is a separate future artifact and must not be mislabeled as `.iso`.
