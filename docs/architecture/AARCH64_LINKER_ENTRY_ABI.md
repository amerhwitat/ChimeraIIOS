# AArch64 kernel linker/entry contract (requirements, not a production linker script)

Status: architecture-port specification. This document is not an implementation of an AArch64 boot path and must not be used to label an x86-64 image as AArch64.

## Linker script requirements

A production script must be reviewed together with the actual AArch64 reset/firmware entry code and memory map. It must define:

- `OUTPUT_FORMAT(elf64-littleaarch64)` and `OUTPUT_ARCH(aarch64)` for the selected little-endian profile; reject big-endian builds unless separately supported.
- An explicit `ENTRY(kernel_entry)` matching a symbol implemented by the real entry assembly.
- A documented `KERNEL_LOAD_ADDRESS` and physical-versus-higher-half virtual mapping policy. Do not invent a load address independent of the bootloader/firmware handoff.
- `PHDRS` with intentional executable/read-only/writable `PT_LOAD` segments; page-aligned boundaries and no W+X segment unless explicitly justified and reviewed.
- Explicit placement of boot entry sections, `.text`, `.rodata`, `.data`, `.bss`, init arrays if used, per-CPU data, and stack reservations. `.bss` must be zeroed before C/C++ runtime assumptions depend on it.
- Exported bounds for image, text, rodata, data, bss and reserved stacks; the loader and memory manager must consume the same definitions.
- A clear relocation policy: either a fixed physical load contract or a defined relocation table/PIE model. Do not claim relocation support solely because the ELF is ET_DYN.
- Discard or explicitly account for unsupported metadata sections, while preserving unwind/debug data when the selected build requires it.

## Entry and exception-vector requirements

- Document entry exception level (EL1/EL2), stack ownership/alignment, MMU/cache state, interrupt mask state, register contract, and platform-information pointer. Never assume firmware starts at one EL without checking/transitioning according to the selected profile.
- Establish a valid stack and clear/initialize required state before calling compiled code. Handle EL transition, translation regime, cache maintenance and barriers in architecture-specific assembly.
- Exception vector base must satisfy the AArch64 architectural alignment requirement: `VBAR_ELx` base aligned to 2 KiB. The vector table must contain correctly aligned vector slots and cover the required current/lower-EL and SP0/SPx exception classes.
- Set `VBAR_EL1` or `VBAR_EL2` only after the corresponding exception-level setup is valid. Establish exception stacks, save/restore the required register frame, and avoid using uninitialized per-CPU state in early vectors.
- Validate the device-tree or other platform handoff pointer and memory ranges before dereferencing; establish timer/interrupt-controller support before enabling interrupts.
- EFI loader is a separate PE/COFF application with an appropriate EFI subsystem and AArch64 machine type. It is not the kernel ELF and must have its own build and validation pipeline.

## Promotion gate

A linker-script compile is not boot acceptance. Require ELF header/program-header inspection, entry-symbol verification, segment range and alignment checks, boot under a named AArch64 UEFI or firmware profile, exception/trap tests, user-mode entry, and immutable artifact hashes. Until those exist, keep `aarch64.release_supported=false`.
