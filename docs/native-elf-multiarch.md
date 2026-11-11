# Native ELF multi-architecture contract

This is an architecture inventory and fail-closed artifact-selection contract, not a claim that every listed architecture already has a working kernel or userspace port.

## Firmware and CPU detection

BIOS versus UEFI describes the firmware entry path, not the CPU ISA. The bootloader must select a boot path compatible with the firmware and only load a kernel/user ELF whose ELF class, endianness, `e_machine`, ABI, and required CPU features match the actual execution environment. On x86, CPU capabilities can be checked with CPUID; on non-x86 platforms, use architecture-specific firmware data such as the device tree and/or UEFI architecture/processor protocols where defined. Never infer AArch64 from “UEFI” alone, and never execute a mismatched image.

## Build and runtime boundaries

- The matrix currently marks x86-64 as the repository build target only. This is not proof of complete process execution or target acceptance.
- All other CPU entries are explicitly `port-required`; adding a row does not create a compiler backend, kernel entry, context switch, syscall ABI, interrupt controller, page-table implementation, timer, SMP bring-up, or native userspace.
- Each new port needs an architecture-specific cross compiler/linker, startup code, linker script, interrupt/trap entry, MMU/page tables, syscall ABI, process context save/restore, scheduler integration, atomic primitives, timer, firmware/boot path, device drivers, and hardware/VM tests.
- A native ELF must be built for each architecture. A host-built binary, a test probe, an ELF header fixture, or a catalogue row is not a production init.
- WASM is listed only to make the distinction explicit: it is a virtual ISA requiring a runtime, not a native CPU boot target.
- Do not use a universal ELF binary for heterogeneous CPU architectures. Package per-architecture kernel and userspace images and have the bootloader select only a verified matching image; fail with a diagnostic when no compatible image exists.

## Validation

```sh
python3 scripts/arch/verify_elf_matrix.py
python3 -m unittest discover -s tests/arch -v
python3 scripts/arch/verify_elf_matrix.py --artifacts <directory>
```

The artifact mode is intentionally fail-closed and requires an actual `x86_64.elf` matching ELF64/little-endian/EM_X86_64. Header identity verification alone does not prove that the file is loadable, executable, safe, or functionally accepted. Final release still requires the existing six target/firmware runtime traces, service health, persistent installer/recovery postconditions, and genuine AP-backed SMP evidence for each claimed platform.
