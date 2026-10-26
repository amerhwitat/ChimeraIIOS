# Offline artwork and native boot assets

The source artwork remains in the OS-specific asset directories:
- Aurora desktop and library artwork: `desktop/aurora/assets/`
- Marine desktop artwork (where provided): `desktop/marine/assets/`
- Firmware/boot splash artwork: `boot/splash/`
- Additional visual boot assets: `boot/visual/`

The ISO build runs `tools/package_os_assets.py` to create an offline bundle:
- `embedded-artwork.json`: Base64-encoded artwork payloads with source path, media type, byte size, and SHA-256.
- `artwork/`: byte-identical copies of source artwork for consumers that prefer files.
- `binaries/`: validated build-produced ELF and PE/COFF EFI files, copied byte-for-byte and identified by SHA-256.
- `binary-manifest.json`: inventory of packaged executable payloads.

Generated ELF/EFI files are produced by the target toolchain during the build; this repository tracks their source and deterministic packaging process rather than checking in unreviewed, toolchain-dependent build outputs. The CI bundle is an auditable build artifact, not by itself proof of runtime acceptance. The final ISO build stages the bundle under `/boot/visual/embedded-artwork.json`, `/boot/chimera/native-binaries/`, and `/usr/share/chimera/assets/offline-artwork/` (OctavianOS uses the same paths in its ISO root).
