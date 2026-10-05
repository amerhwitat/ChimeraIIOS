# Emulator & ROM Inventory

This directory defines the ChimeraIIOS emulation asset model.

## Files

- `known-emulators.json` — normalized emulator/system capability mapping.
- `../README.md` — subsystem architecture and publication policy.

## Local catalog

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\emulation\scan-roms.ps1 -Root "C:\tmp\ChimeraIIOS\ROMs"
```

The command recursively scans the Windows directory and creates local catalogs containing filenames, sizes, timestamps, SHA-256 hashes, detected systems, and likely emulator candidates.

## Matching

The scanner performs deterministic extension/system detection first. The compatibility manager then maps systems to known emulator capabilities. Exact version compatibility, BIOS requirements, CPU architecture, and license/provenance must be verified before a binary is published or launched.

## Publishing

Generated `*.local.json` catalogs are ignored by Git. They can safely describe a local collection without redistributing its contents.

Only assets for which redistribution is authorized should enter `emulation/roms/authorized/` or `emulation/emulators/`. Those paths are configured for Git LFS.
