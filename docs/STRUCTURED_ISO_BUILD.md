# Structured ISO Build and Boot Architecture

The Chimera II ISO pipeline now has a reproducible structured staging phase before ISO mastering. The design follows the existing Spit Fire/Jasper/Koronos architecture while retaining the working Multiboot2 bootstrap.

## Boot sources

`boot/spitfire/` contains SF0 BIOS assembly, SF1 long-mode transition assembly, SF2 freestanding C++ loader code, a shared boot ABI, and the UEFI SFU source contract. `kernel/arch/x86_64/` contains the Koronos entry/linker contract.

## ISO structure

The staging tree contains:

```text
/boot/spitfire
/boot/jasper
/boot/koronos
/boot/grub
/EFI/BOOT
/EFI/CHIMERA
/chimera/applications
/chimera/docs
/chimera/knowledge
/chimera/manifests
/chimera/toolchains
/src
/checksums
```

The final media is ISO 9660 with El Torito boot metadata. `grub-mkrescue` is the preferred authoring backend because its GRUB installation can provide both BIOS and UEFI boot entries; `xorriso` is required by the GRUB authoring path. Standard UEFI media uses `EFI/BOOT/BOOTX64.EFI`.

## Verification

The build verifies the staged tree and writes SHA-256 file manifests before mastering. CI additionally assembles SF0 and requires exactly 512 bytes ending in `55 AA`. QEMU is installed in CI for future serial boot tests; absence of a local QEMU/toolchain is reported rather than treated as a successful boot.

## Scope boundary

The current executable ISO kernel remains the existing Multiboot2 bootstrap. The new Spit Fire stages are integrated source artifacts and handoff contracts; full bare-metal filesystem, networking, security, Aurora and 8192-bit hardware implementations remain separate development layers. The R8192/C8192 processor is explicitly an experimental virtual architecture.
