# Docker bootable ISO builder

This directory provides a reproducible Linux container for producing a GRUB/Multiboot2 ISO from the Chimera II OS repository.

## Pipeline

1. Ubuntu 24.04 container installs the C/C++/ASM and ISO toolchain.
2. The repository is copied into the builder image.
3. If `boot/kernel.bin` exists, it is used directly.
4. Otherwise the existing `boot/iso/build-iso.sh` pipeline builds the repository's Multiboot2 bootstrap kernel and uses `boot/iso/dist/chimera2os.elf` as the kernel input.
5. `tools/build/create-bootable-iso.sh` stages:

   ```text
   iso_root/
   └── boot/
       ├── grub/
       │   └── grub.cfg
       └── kernel.bin
   ```

6. `grub-mkrescue` creates `/output/output.iso`; `xorriso` is used to inspect the resulting El Torito/system-area metadata.
7. `/output/output.iso.sha256` is produced by the ISO creation script.

## Build

From the repository root:

```bash
docker build -f docker/iso/Dockerfile -t chimera-ii-os-iso .
docker run --rm -v "$PWD/docker-output:/output" chimera-ii-os-iso
```

The resulting files are written to `docker-output/` on the host.

## Explicit kernel

To use a separately compiled Multiboot2-compatible kernel:

```bash
docker run --rm \
  -e CHIMERA_KERNEL=/src/boot/kernel.bin \
  -v "$PWD/docker-output:/output" \
  chimera-ii-os-iso
```

For an externally supplied kernel, mount it into the container and set `CHIMERA_KERNEL` to its container path. `kernel.bin` must be a real Multiboot2-compatible boot image; an arbitrary ELF/PE executable is not sufficient.

## Build without automatic kernel compilation

If a kernel is already present and you want the container to fail instead of attempting the bootstrap build when it is missing:

```bash
docker run --rm -e CHIMERA_BUILD=never -v "$PWD/docker-output:/output" chimera-ii-os-iso
```

## Notes

- The existing top-level `Dockerfile` remains the general application/container image. The ISO builder is deliberately isolated under `docker/iso/` so the two workflows do not conflict.
- No host disk is partitioned or flashed by this workflow.
- The container does not require `--privileged` for ISO creation.
- `grub-mkrescue` is the authoring command used by the canonical ISO script; `xorriso` supplies the ISO mastering backend and is also used for post-build inspection.
