# Retro machine integration: Amiga and Commodore

Provides emulator launch profiles and lawful starter media for Amiga 500, Amiga 2000 and Commodore 64.

- Amiga: FS-UAE first, then RetroArch + PUAE libretro core.
- C64: VICE x64sc/x64 first, then MAME.
- Kickstart ROMs, Workbench disks, commercial games and proprietary firmware are not included.
- Generated ADFs are formatted OFS/FFS data disks with starter documentation/configuration, not a Workbench replacement or preinstalled commercial OS.

Install `amitools` (xdftool) and VICE (c1541), then run `retro/commodore/create-retro-media.sh --out build/retro-media`.

Produces CHIMERA-Amiga-500.adf, CHIMERA-Amiga-2000.adf and CHIMERA-Commodore-64.d64. The C64 disk contains an original BASIC demo. All images are listed and SHA-256 verified after creation.

Launch with `retro/commodore/launch-machine.sh amiga-a500 disk.adf`, `amiga-a2000`, or `commodore-c64 disk.d64`. Set CHIMERA_KICKSTART_ROM to a legally obtained Kickstart ROM for Amiga.
