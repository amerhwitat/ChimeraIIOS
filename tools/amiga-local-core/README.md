# Chimera II Amiga Local Core

This directory is intentionally outside `web/`. GitHub Pages must never package the Amiga emulator core, Kickstart ROMs, disks or firmware.

## Local build

```bash
./tools/amiga-local-core/build-local-core.sh
```

The build uses the open-source PUAE libretro source and produces a native local core. User-supplied Kickstart ROMs and Amiga content remain outside the repository and outside the Pages deployment.

## Local bridge

```bash
python3 tools/runtime/chimera-local-bridge.py
```

The Aurora Control Center uses `tools/runtime/chimera-local-bridge.py` on `127.0.0.1:8765`; it launches FS-UAE with the selected A500/A2000 model and also exposes the VICE Commodore launcher. The older direct PUAE helper, if used independently, listens on `127.0.0.1:8766` to avoid colliding with the main runtime bridge. Neither bridge accepts arbitrary shell commands.

## Content

Supported content includes ADF/ADZ/DMS/FDI/IPF, HDF/HDZ, LHA/WHDLoad, M3U and supported CD formats. Firmware remains user-provided.

## Boundary

- Pages: HTML/CSS/JS/catalogs only.
- Local machine: emulator core, RetroArch/frontend, firmware and user-owned content.
- Browser database: settings, favorites, input profiles and local game metadata only.
