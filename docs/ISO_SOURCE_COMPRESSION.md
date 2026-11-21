# Compressed source payloads on the Chimera II OS ISO

The large ISO build keeps boot-critical files and runtime executables directly readable by the boot/runtime path, while repository source material is stored as a compressed, checksummed archive.

## Format

- Archive: `/source/chimera-source.tar.zst`
- Container: POSIX tar
- Compression: Zstandard (`zstd`), default level 19, multi-threaded (`-T0`)
- Manifest: `/source/chimera-source-manifest.json`
- Checksum: `/source/chimera-source.tar.zst.sha256`
- The source archive is documentation/development material and is **not** boot-executable.

## Build

Use the large-build wrapper:

```bash
bash tools/iso/build-large-iso-with-compressed-source.sh --storage-auto
```

The wrapper preserves the existing `build-chimera-iso.sh` implementation and injects source compression immediately before SquashFS creation. Set `CHIMERA_COMPRESS_SOURCE=0` to disable the injected source stage.

## Extraction

On a running Chimera II OS system:

```bash
mkdir -p /tmp/chimera-source
zstd -dc /source/chimera-source.tar.zst | tar -xpf - -C /tmp/chimera-source
```

## What is excluded

Build directories, Git metadata, caches, virtual environments, dependency trees such as `node_modules`, generated ISOs/images/SquashFS files, logs, and common private key/certificate extensions are excluded. This prevents the ISO source archive from recursively capturing build output or credentials.

## Verification

```bash
bash tools/iso/verify-source-compression.sh build/iso
```

The verifier checks the SHA-256 checksum, validates the Zstandard stream, and confirms the normalized `ChimeraIIOS/` archive root without extracting the archive into the ISO staging tree.
