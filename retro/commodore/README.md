# Amiga and Commodore retro runtime

## Supported machine profiles
- Amiga 500 (Motorola 68000; ADF floppy media)
- Amiga 2000 (Motorola 68000; ADF floppy media)
- Amiga 4000 (68020/030/040 variants; ADF floppy media)
- Commodore 64 (MOS 6510; D64 floppy media)

## Build original disk images
```sh
sudo apt-get install vice
python3 -m pip install --user --break-system-packages amitools
export PATH="$HOME/.local/bin:$PATH"
bash retro/commodore/create-retro-media.sh --out build/retro-media
```

The ADFs are Amiga Fast File System disks containing original documentation and the
machine profile, including an A4000/040 profile. The D64 contains an original BASIC V2 demo. CI verifies the ADF
filesystem listings, D64 directory, image sizes and SHA-256 checksums.

## Build emulator providers
```sh
bash retro/commodore/build-emulator-providers.sh --out build/retro-emulators --jobs 2
```

The build pins PUAE/libretro and VICE source revisions, compiles the Amiga core and
VICE C64 tools (`x64sc`), checks ELF headers and shared-library dependencies, and writes
checksums. Run the launcher with `retro/commodore/launch-machine.sh`.

No copyrighted Kickstart ROM, Workbench disk, commercial firmware or game content
is included. A genuine Kickstart ROM is optional for PUAE when its built-in AROS
replacement is used; users must supply any proprietary firmware they choose to use.
