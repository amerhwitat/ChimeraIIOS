# Online DOS application/game discovery and ISO payload policy

The build can refresh a metadata-only catalog from the official FreeDOS games
index and can stage reviewed packages through the same DOSBox/DOSBox-X adapter
used by command shells and Aurora.

## Discover online titles during a build

```sh
./build-chimera-iso.sh --refresh-online-catalogs
```

This refreshes the existing online indexes and saves the DOS discovery metadata
to `build/dos-online-discovery.json`; the ISO layout copies it to
`/usr/share/chimera/commands/ONLINE-DISCOVERY.json`. For a metadata-only refresh
without the rest of the build:

```sh
python3 tools/commands/dos-payload-builder.py discover --output build/dos-online-discovery.json
```

This records links/titles only. It does not download binaries or grant permission
to redistribute them. Catalog entries are leads, not proof of compatibility.

## Include approved payloads in an ISO

The ISO layout step always stages any already-cached payloads whose manifest
entries pass every gate. To permit downloads for such entries during a build:

```sh
./build-chimera-iso.sh --sync-dos-payloads
```

A package is eligible only when its manifest entry has all of:
- `status: "smoke-tested"`, `license_reviewed: true`, `smoke_tested: true`;
- `redistributable: true` and a specific license identifier;
- exact HTTPS package URL on an approved FreeDOS/ibiblio host;
- exact SHA-256 and ZIP format.

Cache archives at `build/dos-payload-cache/<id>.zip`. SHA-256 is checked before
extraction. ZIP paths, symlinks, file size and file extensions are constrained.
Only DOS-relevant file extensions are staged into
`/usr/share/chimera/dos/apps/<id>`; an index is written to `CATALOG.json`.
The adapter/emulator can launch staged `.COM`, `.EXE` and `.BAT` files. The
installer must keep DOSBox/DOSBox-X installed for launch support.

No legacy commercial title, proprietary game data, abandonware, or package with
unclear redistribution rights is included automatically. A title is not called
working until the exact staged binary has a recorded smoke test on a supported
emulator profile. Catalog refresh and payload fetching are separate operations.

Run tests with:
```sh
python3 tools/commands/test-dos-payload-builder.py
```
