# Chimera II OS bootable ISO

This directory defines the reproducible **bootstrap ISO** build. It boots through GRUB2/Multiboot2 and enters a tiny freestanding C kernel stub. The stub is intentionally separate from the host-emulated full Chimera II services.

Build prerequisites on Linux:
- `grub-mkrescue`
- `xorriso`
- `gcc` with freestanding 32-bit support
- `ld`

Run `./build-iso.sh` to produce `dist/chimera2os-bootstrap.iso`.

The ISO is a bootable engineering artifact, not yet a claim that every Koronos service, driver, filesystem and Aurora component is bare-metal complete. Those components remain incrementally integrated behind the bootstrap boundary.
