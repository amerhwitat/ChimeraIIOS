# ChimeraIIOS Emulator Catalog

The catalog separates **detected media**, **detected emulator binaries**, **BIOS candidates**, and **compatibility mappings**.

## Local scan

Default Windows source:

`C:\\tmp\\ChimeraIIOS\\ROMs`

Run:

`powershell -ExecutionPolicy Bypass -File .\\tools\\emulation\\scan-roms.ps1`

Generated local-only files:

- `roms.local.json`
- `emulators.local.json`
- `bios.local.json`
- `compatibility.local.json`

The scanner is recursive and records SHA-256, size, relative path, extension, detected system and provenance. Emulator matching is resolved against `known-emulators.json`, not just executable filenames.

BIOS classification is deliberately marked heuristic unless a content-signature database is available.

## Publication

Do not commit or publish commercial/copyrighted ROMs, BIOS images, keys, firmware, or other material without redistribution rights. Unknown material remains metadata-only.

Authorized large binaries belong under the repository's Git LFS policy. Emulator binaries must comply with their licenses.
