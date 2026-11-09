# Retro machine integration: Amiga and Commodore

Provides emulator launch profiles and lawful starter media for Amiga 500, Amiga 2000 and Commodore 64.

- Amiga: FS-UAE first, then RetroArch + PUAE libretro core.
- C64: VICE x64sc/x64 first, then MAME.
- Kickstart ROMs, Workbench disks, commercial games and proprietary firmware are not included.
- Generated ADFs are formatted OFS/FFS data disks with starter documentation/configuration, not a Workbench replacement or preinstalled commercial OS.

Install `amitools` (xdftool) and VICE (c1541), then run `retro/commodore/create-retro-media.sh --out build/retro-media`.

Produces CHIMERA-Amiga-500.adf, CHIMERA-Amiga-2000.adf and CHIMERA-Commodore-64.d64. The C64 disk contains an original BASIC demo. All images are listed and SHA-256 verified after creation.

Launch with `retro/commodore/launch-machine.sh amiga-a500 disk.adf`, `amiga-a2000`, or `commodore-c64 disk.d64`. Set CHIMERA_KICKSTART_ROM to a legally obtained Kickstart ROM for Amiga.

## Open-source emulator providers

The build script compiles pinned upstream sources:
- PUAE / libretro-uae: `d366f77c60e5a5f059f129cc3773d3048306083b` (GPL-2.0)
- VICE: `635853a38f93e2d5da8d0c9ea42a30ad60f52fe6` (GPL-2.0)

Upstream projects: https://github.com/libretro/libretro-uae and https://github.com/VICE-Team/svn-mirror. The PUAE core exposes A500 and A2000 models and supports ADF media. The VICE build provides the C64 emulator and c1541 disk utility. CI checks the compiled ELF headers, shared-library dependencies and SHA-256 hashes before publishing artifacts.

Build the emulator providers with `retro/commodore/build-emulator-providers.sh --out build/retro-emulators --jobs 2`. The emulator artifacts are Linux x86_64 CI outputs; they are not claimed to be Windows/macOS binaries.
