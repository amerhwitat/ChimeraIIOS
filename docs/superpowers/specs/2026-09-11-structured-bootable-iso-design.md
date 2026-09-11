# Chimera II Structured Bootable ISO Design

## Goal
Upgrade Chimera II OS from a bootstrap Multiboot-only ISO into a reproducible, structured hybrid boot-media pipeline while preserving the existing bootstrap path.

## Evidence and design basis
Library research identified the existing Chimera II low-level design for Spit Fire SF0/SF1/SF2/SFU, `chm_bootinfo_t`, CPU capability profiles, Jasper, Koronos, and QEMU testing. The architecture poster independently describes BIOS/MBR, GPT/UEFI, ARM, memory maps, ISA/toolchain flow, and the 8192-bit execution model. The redesign report recommends UEFI/GPT as the preferred production path and BIOS/MBR as compatibility, with signed/measured boot as future security layers.

## Architecture
1. **Spit Fire boot chain**
   - SF0: 16-bit BIOS MBR stub, exactly 512 bytes with `0xAA55` signature, loads SF1 with INT 13h extensions.
   - SF1: protected/long-mode transition and handoff contract.
   - SF2: freestanding C/C++ loader contract and `chm_bootinfo_t` construction.
   - SFU: UEFI PE/COFF loader source and headers, built only when a UEFI toolchain is available.
2. **Boot ABI**
   - Central C-compatible `bootinfo.h` defines architecture, encoding, feature flags, framebuffer, memory map, initrd, command line, EFI and ACPI pointers.
   - Versioned ABI with compile-time size/alignment checks.
3. **Structured ISO tree**
   - `/boot/spitfire`, `/boot/jasper`, `/boot/koronos`, `/EFI/BOOT`, `/EFI/CHIMERA`, `/chimera/{docs,manifests,applications,toolchains,knowledge}`, `/src`, and `/checksums`.
   - BIOS El Torito boot entry and UEFI El Torito FAT image are emitted when the host tooling supports them.
   - xorriso is preferred for hybrid ISO authoring; `grub-mkrescue` remains a fallback for environments without the advanced authoring path.
4. **Kernel and ISA integration**
   - Add low-level source/header/linker artifacts for Spit Fire and Koronos without claiming that every research subsystem is already bare-metal production-ready.
   - Keep R8192/C8192 and RegisterN components as research/virtual targets.
5. **Verification**
   - Validate boot-sector size/signature, ELF existence, ISO 9660 presence, expected directory tree, checksums, and Multiboot2 header.
   - QEMU tests are optional environment-gated checks; missing QEMU/toolchains produce explicit skipped results rather than false passes.

## Image requirements
The ISO is a real ISO 9660 filesystem with El Torito boot metadata. BIOS uses a no-emulation boot image; UEFI uses a FAT EFI System Partition image at the standard `EFI/BOOT/BOOTX64.EFI` path. Where xorriso supports it, the ISO is authored as a BIOS+UEFI hybrid suitable for optical media and USB-style boot workflows. This follows the documented El Torito model and avoids representing a raw `.img` copy as a partitioned disk image.

## Source additions
- NASM x86 boot stages and linker scripts.
- Freestanding C/C++ boot loader interfaces.
- UEFI C entry-point source and EFI compatibility headers.
- Shared Chimera boot ABI headers.
- Kernel entry/linker contract and a minimal Koronos handoff stub.
- Structured ISO manifest and validation tooling.

## Safety and scope
No arbitrary Internet code is copied into executable boot stages. External/library material is treated as design evidence. Downloaded toolchains and packages remain explicit, provenance-aware build inputs. Research claims such as 8192-bit physical silicon remain clearly labeled as virtual/experimental.

## Success criteria
- One deterministic build command stages a structured Chimera II ISO tree.
- BIOS bootstrap remains functional through the existing Multiboot2 path.
- UEFI structure is emitted when an EFI loader and ISO authoring backend are available.
- Build metadata, source manifests and SHA-256 checksums are embedded.
- CI can validate structure without requiring a privileged host or physical hardware.
