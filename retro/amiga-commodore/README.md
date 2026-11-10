# Amiga and Commodore media for Chimera II OS

This directory builds real emulator media rather than empty placeholder files.

## Amiga 500 / Amiga 2000

- Output: `AROS-Amiga-500-2000-m68k-boot.adf`
- Format: 880 KiB Amiga Disk File (ADF).
- CPU family: Motorola 68000; the same AROS m68k boot floppy targets the A500/A2000 class.
- Source: the official AROS nightly `amiga-m68k-boot-floppy` image.
- The AROS boot floppy is an open-source Amiga-compatible OS boot medium. It is not a copy of proprietary AmigaOS or a Kickstart ROM.

## Commodore 64

- Output: `CHIMERA-Commodore-64.d64`
- Format: D64 (1541 disk image), **not ADF**. The Commodore 64 does not use Amiga ADF media.
- Contains `CHIMERA64.PRG`, a tokenized BASIC V2 program built by this repository and checked using VICE's `c1541`.

## Build and verify

```bash
sudo apt-get install python3 vice unzip
python3 retro/amiga-commodore/build_media.py --out build/retro-media
python3 retro/amiga-commodore/verify_media.py build/retro-media
c1541 -attach build/retro-media/CHIMERA-Commodore-64.d64 -list
```

For an Amiga emulator, use FS-UAE or WinUAE and mount the ADF as DF0. For the C64, use VICE `x64sc` and attach the D64 as drive 8. AROS provides an open-source ROM/OS path; do not substitute copyrighted Kickstart images from untrusted download sites.

The CI artifact contains the two disk images, the C64 program, and a SHA-256/provenance manifest. A successful structural check does not claim that the Amiga guest has been booted in a full emulator; emulator boot acceptance is a separate test.

## Upstream and licensing

- AROS nightly downloads: https://sourceforge.net/projects/aros/files/nightly2/
- AROS project: https://aros.org/
- AROS Public License: https://aros.org/license/
- VICE: https://vice-emu.sourceforge.io/
- VICE source: https://github.com/VICE-Team/svn-mirror

Only the official AROS m68k floppy is redistributed by the build. Commercial Amiga/Commodore ROMs and commercial software are not downloaded or included.
