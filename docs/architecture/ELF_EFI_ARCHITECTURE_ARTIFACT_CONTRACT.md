# ELF and EFI architecture artifact contract

Status: **porting contract; not a claim that every target has a bootable kernel or EFI loader**.

This document is shared by ChimeraIIOS and OctavianOS. Keep the same target IDs and acceptance rules in both repositories. Do not copy a binary from one ISA/ABI to another, and do not treat a generic test ELF as the production kernel or init.

## Artifact classes (must remain distinct)

1. **Kernel ELF** — freestanding kernel image built from the target's architecture port, with the correct ELF class, machine, endianness, ABI, entry point, and linker script.
2. **Userspace ELF** — target-ABI executable with matching syscall ABI, relocations, address-space layout and loader support. A successful compile does not prove that it can run.
3. **EFI application** — PE/COFF image with the correct machine type, EFI subsystem, calling convention, firmware ABI and removable-media path. An ELF file renamed to `BOOTX64.EFI` is invalid.
4. **Legacy BIOS stage** — only for firmware/architectures with a separately implemented and tested BIOS boot contract. BIOS is not a portable interface for ARM/RISC-V/etc.
5. **Probe/fixture** — test-only artifact; never place it in a production kernel/init slot or use it as readiness evidence.

## Target inventory

| Target ID | ELF/toolchain family | EFI candidate | Current repository posture | Required before promotion |
|---|---|---|---|---|
| `x86_64` | `x86_64-elf` or project-approved cross target | X64 PE/COFF | Primary boot pipeline, production release still blocked | Kernel + loader + EFI handoff, all six target/firmware traces, services/UI, installer persistence, recovery and SMP evidence |
| `i386` | `i686-elf` | IA32 PE/COFF only where firmware supports it | Probe/porting target; not release accepted | 32-bit kernel, paging/interrupt/syscall ABI, matching loader, BIOS/UEFI boot tests |
| `aarch64` | `aarch64-elf` | ARM64 PE/COFF on supported UEFI platforms | Porting target | EL transition, exception vectors, timer/interrupt controller, device tree, drivers, userspace and QEMU/board traces |
| `armv7` | `arm-none-eabi` or approved Linux ABI as applicable | Firmware-specific; not assumed | Porting target | Defined platform/ABI, exception and MMU setup, boot chain, drivers and userspace tests |
| `riscv64` | `riscv64-unknown-elf` | Only for an explicitly supported RISC-V UEFI firmware target | Porting target | SBI/firmware contract, privilege transition, trap/timer/interrupt paths, device tree, drivers and userspace traces |
| `riscv32` | `riscv32-unknown-elf` | Firmware-specific; not assumed | Research target | Complete architecture port and a defined firmware/machine acceptance profile |
| `mips64` | ABI-specific MIPS cross toolchain | Not assumed | Research/emulation target | ABI/endian profile, exception/MMU port, firmware contract, drivers and boot evidence |
| `powerpc64` | ABI-specific PowerPC cross toolchain | Platform-specific; not assumed | Research/emulation target | ELFv1/ELFv2 selection, exception/MMU port, firmware contract, drivers and boot evidence |
| `loongarch64` | `loongarch64-unknown-linux-gnu` or project-approved target | Only with matching firmware support | Research target | Kernel/loader port, ABI, interrupt/timer, drivers and boot evidence |
| `s390x` | `s390x-linux-gnu` or freestanding target | Platform-specific; not assumed | Inventory target, not accepted | Defined boot firmware and loader, architecture port, drivers and runtime evidence |
| `sparc64` | ABI-specific SPARC cross toolchain | Not assumed | Inventory target, not accepted | Defined platform, architecture port, loader, drivers and runtime evidence |

This list is a maintained porting inventory, not a promise of support for every CPU model or every member of an ISA family. Add targets only with an explicit ABI, firmware/machine profile, compiler triple, linker script and reproducible test.

## Build and packaging invariants

- Keep outputs segregated by target and artifact type, e.g. `artifacts/<target>/kernel.elf`, `artifacts/<target>/userspace/`, and `artifacts/<target>/efi/BOOT*.EFI`. Never share one output directory across target triples.
- Record compiler version, target triple, flags, linker script, source revision, ELF/PE machine, hashes and test evidence in a manifest.
- Validate ELF magic, class, data encoding, machine, type, entry point and load segments before packaging. Validate PE/COFF machine and EFI subsystem for EFI images.
- Firmware selection must use a validated platform/firmware profile and artifact metadata; never infer CPU ISA from BIOS-versus-UEFI alone. BIOS/UEFI identifies firmware mode, not the processor architecture.
- Refuse to package a target if its kernel, loader, EFI application, rootfs and userspace ABI do not match. No fallback to an x86-64 image on a different ISA.
- Cross-compilation success is build evidence only. Boot, ring-3 execution, syscall/memory safety, storage, services, GUI, recovery and SMP remain separate runtime gates.
- Do not check generated binaries into source control as a substitute for reproducible builds. Publish signed/checksummed CI artifacts only after their own target-specific tests pass; production ISO publication remains gated by DAPS.

## Promotion checklist per target

1. Toolchain and ABI are pinned and reproducible.
2. Kernel ELF and every userspace ELF pass machine/class/ABI validation.
3. EFI image is genuine PE/COFF with correct machine/subsystem, or a separately verified BIOS loader is used where applicable.
4. Firmware/emulator boots the matching image and logs the selected target and artifact hashes.
5. User-mode transition, syscall ABI, memory permissions, scheduler/process lifecycle and file I/O pass runtime tests.
6. Target-specific services and desktop/installer/recovery postconditions pass.
7. Evidence is immutable and linked from the support matrix. Until then, `release_supported` remains false.
