# Chimera Retro Media Builder

Creates three reproducible media images:

- \`Chimera-Amiga-A500.adf\`: 880 KiB OFS data floppy.
- \`Chimera-Amiga-A2000.adf\`: 880 KiB FFS data floppy.
- \`Chimera-Commodore-C64-Starter.d64\`: standard 35-track D64 with an original BASIC V2 starter program.

## Build and validate

\`\`\`sh
sudo apt-get install python3-venv vice
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip amitools
python tools/retro-media/build_retro_media.py --output build/retro-media
CHIMERA_RETRO_MEDIA_DIR="$PWD/build/retro-media" python -m unittest discover -s tests/retro_media -v
\`\`\`

Amiga images are formatted and inspected by \`xdftool\` from amitools. The D64 is created, directory-listed and PRG-round-tripped with VICE's \`c1541\`. CI publishes the generated images as an artifact.

## Firmware and compatibility boundary

No Kickstart ROM, Workbench distribution, Commodore KERNAL/BASIC ROM, commercial game, or proprietary firmware is included. Amiga emulation requires a legally licensed/user-provided Kickstart ROM; a full Workbench desktop also requires licensed Workbench files. VICE requires the appropriate ROM set or an independently licensed replacement. These are formatted media images, not complete standalone OS installations.

## Upstream projects

- FS-UAE: https://fs-uae.net/ (GPL family).
- VICE: https://vice-emu.sourceforge.io/ (GPL-2.0-or-later).
- amitools / xdftool: https://amitools.readthedocs.io/ (retain upstream notices).

## Installing the local emulator runtimes

On Debian/Ubuntu-derived Chimera II OS or OctavianOS, run:

\`\`\`sh
sudo bash tools/retro-media/install-emulators.sh
\`\`\`

The installer uses the distribution packages for FS-UAE and VICE. FS-UAE's A2000 profile
uses its A500 base machine with the documented A2000 chipset-compatibility setting; this is
not a claim of bit-for-bit emulation of every A2000 expansion board. Firmware remains
user-supplied/licensed.
