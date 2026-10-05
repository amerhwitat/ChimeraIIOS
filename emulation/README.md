# ChimeraIIOS Emulator & ROM Integration

This subsystem inventories emulator binaries and ROM/media files found in the local ChimeraIIOS ROM workspace and records deterministic metadata for Aurora/Koronos integration.

## Local source

The Windows scanner defaults to:

`C:\\tmp\\ChimeraIIOS\\ROMs`

Run from the ChimeraIIOS repository:

```powershell
powershell -ExecutionPolicy Bypass -File .\\tools\\emulation\\scan-roms.ps1
```

The scanner recursively inventories files, calculates SHA-256 hashes, detects common ROM/media formats, identifies likely emulator executables, and produces:

- `emulation/catalog/roms.local.json`
- `emulation/catalog/emulators.local.json`
- `emulation/catalog/compatibility.local.json`

These generated local catalogs are intentionally ignored by Git by default because they may describe proprietary ROMs.

## Publishing policy

Do not commit or publish commercial/copyrighted ROM dumps, BIOS images, or other material unless you have the legal right to redistribute them. Unknown ROMs remain local and are represented by metadata/hashes only.

Open-source emulator binaries may be redistributed only according to their licenses. Large authorized binaries should use Git LFS.

## Runtime model

ROM/media -> format/signature -> compatibility catalog -> Emulator Manager -> Aurora -> Koronos capability authorization -> emulator.

The inventory is metadata-first: a ROM does not become executable merely because an emulator supports its file extension.
