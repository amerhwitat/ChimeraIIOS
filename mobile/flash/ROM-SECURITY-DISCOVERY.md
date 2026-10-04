# Chimera II Mobile ROM / Security Discovery

The Mobile Edition Flash Tool now performs exact-device firmware research before a
device-specific Chimera build is considered flashable.

## Workflow

1. Detect one authorized Android device with ADB and collect manufacturer, model,
   codename/product, board, SoC, ABI, Android version, build fingerprint,
   security-patch level, bootloader state, Verified Boot state, slot and vbmeta
   device state.
2. Match the device against an exact Chimera profile. No "similar" model is
   accepted.
3. Search the public web using the exact device identifiers.
4. Rank/download only direct archive candidates from the configured official
   vendor/project allow-list.
5. Record SHA-256 for every downloaded archive.
6. Extract **public security/verification material only** into
   `build/mobile/rom-discovery/<codename>/security/`: vbmeta images, AVB public
   keys/certificates, signatures, hashes, signed metadata and rollback metadata.
7. Never extract, request, derive, or store private signing keys, DRM credentials,
   authentication tokens, OEM authorization secrets, or other secrets.
8. Feed the resulting catalog into the device-specific Chimera build manifest.
9. Flash remains manifest-driven and requires the existing exact-device,
   signed-image, rollback and explicit-confirmation gates.

## Commands

```bash
tools/mobile/chimera-mobile-flash.sh detect
tools/mobile/chimera-mobile-flash.sh rom-discover
tools/mobile/chimera-mobile-flash.sh build
tools/mobile/chimera-mobile-flash.sh --dry-run
tools/mobile/chimera-mobile-flash.sh flash
```

The GUI exposes the same operation as **Find ROMs + Security**.

## Security boundary

This feature is a firmware research and compatibility layer. It does **not**
unlock an OEM bootloader, bypass Verified Boot/AVB, bypass vendor authentication,
forge signatures, or write arbitrary partitions. A device remains non-flashable
until a matching Chimera device profile provides an approved transport and
partition map.

Google's official Android factory/full-OTA pages are used as reference sources;
Google notes that factory images can erase data and that full OTA packages are
generally safer for supported recovery/update scenarios. Samsung's official
support documentation similarly directs users to Smart Switch/official software
update paths. The tool therefore treats vendor firmware as reference material
for compatibility and recovery rather than as a license to circumvent vendor
security controls.
