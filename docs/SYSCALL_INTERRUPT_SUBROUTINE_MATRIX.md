# Syscall, interrupt, and subroutine implementation matrix

This file is an evidence ledger, not a claim of complete cross-OS compatibility. A syscall name, interrupt vector, exported symbol, generated stub, or catalog row is **not** counted as implemented until its real execution path and tests pass.

## Native Chimera ABI currently declared

Authoritative IDs are in `kernel/include/chimera/syscall.h` (ABI version 1):

| ID | Symbol | Current dispatcher status |
|---:|---|---|
| 1 | `CHM_SYS_EXIT` | Partial: acknowledged; process teardown is not implemented here |
| 2 | `CHM_SYS_GETPID` | **Broken placeholder:** currently returns constant PID 1; must use the current process object |
| 3 | `CHM_SYS_YIELD` | Dispatches scheduler yield; runtime acceptance still required |
| 4 | `CHM_SYS_TIME_TICKS` | Returns kernel timer ticks; runtime acceptance still required |
| 8 | `CHM_SYS_READ` | Declared, returns ENOSYS |
| 9 | `CHM_SYS_WRITE` | Declared, returns ENOSYS |
| 10 | `CHM_SYS_MMAP` | Declared, returns ENOSYS |
| 11 | `CHM_SYS_MUNMAP` | Declared, returns ENOSYS |
| 12 | `CHM_SYS_IOCTL` | Declared, returns ENOSYS |
| 13 | `CHM_SYS_NANOSLEEP` | Declared, returns ENOSYS |
| 14 | `CHM_SYS_WAIT` | Declared, returns ENOSYS |
| 15 | `CHM_SYS_ARCH_PRCTL` | Declared, returns ENOSYS |
| 16 | `CHM_SYS_EXIT_GROUP` | Partial: acknowledged; group teardown is not implemented here |
| 17 | `CHM_SYS_VALIDATE_BOOT_PAYLOAD` | Declared; not dispatched by the current canonical switch |

Do not change existing IDs silently. Add new calls only through the authoritative registry/header, with argument schemas, privilege policy, error conventions, implementation symbol, and tests. Do not mark an operation implemented solely because its ID is recognized.

## Interrupt and exception entry

The current x86-64 contract declares 256 IDT entries, IRQ base 32, native software vector `0x80`, Windows-compatibility identity `0x2e`, and DOS-compatibility identity `0x21` in `kernel/include/chimera/interrupt.h`.

- IDT setup installs DPL0 gates and loads IDTR. The compatibility vector constants do **not** provide ring-3 syscall gates or complete Windows/DOS ABI implementations.
- The common dispatch path records counters and classifies vectors; this is not proof that all exception/IRQ handlers are safe or operational.
- Before production enablement, test all supported exception frames (including CPU-pushed error codes), register preservation, stack alignment, privilege transitions/TSS/RSP0, nested faults, PIC/APIC routing and EOI, timer IRQs, IPIs, per-CPU state, and fault containment.
- Unimplemented vectors must fail safely; do not expose raw device IRQs directly to applications.

## Cross-OS ABI separation

Maintain distinct, versioned personalities for Chimera native, Linux x86-64, Linux i386, each BSD, Darwin BSD syscalls, Mach traps, Windows Win32/NT APIs, and DOS interrupts. Never dispatch foreign numeric IDs directly into the native table. Windows system-service numbers are build-dependent; do not hardcode guessed SSNs. Mark an ABI or operation `unsupported` until a real adapter, validated user entry path, and executable tests exist.

## Subroutine inventory requirements

For each exported kernel/runtime subroutine, record: canonical name, source symbol, ABI/architecture, argument and return schema, privilege/capability requirements, ownership/lifetime, error behavior, implementation status, and test references. Inventory C/C++ exports, assembly entry/exit stubs, interrupt handlers, syscall adapters, driver interfaces, runtime/library APIs, and compatibility-provider APIs separately. Avoid merging similarly named functions from different operating systems into one contract.

## Release acceptance checklist

- [ ] Generated per-OS/per-architecture syscall and subroutine matrix has no duplicate IDs/symbols and links every `implemented` row to source and tests.
- [ ] Unknown and declared-but-unimplemented syscalls return the documented unsupported error; malformed pointers, lengths, handles, and privilege requests are rejected.
- [ ] Ring-3 acknowledgements are proven from real trap frames and bound to the actual process PID (never a constant).
- [ ] Each supported exception/IRQ class has a deterministic test; timer/IPI and AP startup are verified on genuinely concurrent CPUs.
- [ ] Live, Installer, and Recovery each pass BIOS and UEFI production-ISO tests.
- [ ] Storage writes survive unmount and cold reboot; services are supervised; Aurora/session handoff is observed from the real production initramfs path.

**Release rule:** keep the release gate closed until these checks pass. Documentation, generated tables, compilation, candidate ELFs, and emulated sequential CPU runs are not substitutes for runtime evidence.
