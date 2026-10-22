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


## Production ISO Live handoff trace gap (2026-10-22)

Latest recorded OctavianOS full-ISO acceptance run: workflow [39743340747](https://github.com/amerhwitat/OctavianOS/actions/runs/39743340747). Kernel/ISO build and basic routing checks passed; Installer and Recovery satisfied the strict userspace-handoff verifier; Live failed because the trace did not contain the required ordered sequence:

1. `[KRN ] KORONOS READY`;
2. `USER INIT SYSCALL: target=live init_pid=<nonzero PID>` emitted by the actual ring-3 trap/entry path after validating saved CPL, active process, and address space;
3. `USERSPACE READY: live init pid=<same PID>` emitted only after the native init successfully completes the required syscall round-trip.

The failure proves a missing acceptance sequence, **not** which of the possible causes is responsible. Candidate causes include a Live-specific payload/entry fault, a target-routing or image-staging mismatch, an absent trap-path telemetry emission, or a PID/context mismatch. Distinguish them by preserving the raw QEMU debugcon trace and inspecting the exact staged Live ELF, ELF program headers and entry point, page mappings/permissions, ring-3 trap frame, syscall return values, and active process/CR3. Do not infer that the user reached CPL 3 from a pre-entry kernel message.

### ABI guardrails for the remediation

- Do **not** paste an illustrative `int $0x80` syscall implementation with invented IDs into the current native init. The current native init uses the documented x86-64 `syscall` instruction and the constants in `kernel/include/chimera/syscall.h`; `CHM_SYS_EXIT=1`, `GETPID=2`, `WRITE=9`, and `VALIDATE_BOOT_PAYLOAD=17` are the declared native IDs. The `int $0x80` instruction is currently the separate CPL3-entry probe, not a replacement syscall ABI.
- Do not add an invented `SYS_HANDSHAKE=1`, `SYS_EMIT_READINESS=3`, or `SYS_EXIT=99` contract, set process state from userspace, assume PID 1, or print readiness directly from the kernel to satisfy the regex. Such changes would break the existing ABI or fabricate user-originated evidence.
- The dispatcher currently returns a constant PID for GETPID and does not implement WRITE or VALIDATE_BOOT_PAYLOAD in its canonical switch. Those are real ABI gaps to resolve against the actual process manager and user-memory validation; telemetry alone cannot fix them. Do not emit success for unsupported calls.
- Kernel telemetry should be emitted from the validated trap path using the actual current task PID and target identity, with explicit CPL3 evidence. Readiness must remain a userspace-originated write/marker bound to that same PID and must follow the acknowledgement in the trace. Avoid logging arbitrary user pointers as strings; validate/copy bounded buffers before writing them.

### Required close-out evidence

- [ ] Capture and retain the failing Live raw trace and compare it to the passing Installer/Recovery traces.
- [ ] Prove the exact Live payload selected by the production GRUB/ISO path matches the target-specific ELF built and hashed by the release script.
- [ ] Add regression tests for the verifier's ordered markers, target match, same nonzero PID, duplicate/out-of-order markers, and missing markers; keep it fail-closed.
- [ ] Fix the actual Live execution/ABI defect, not just its log format; test bad pointers, unknown syscalls, and PID 0 rejection.
- [ ] Re-run Live, Installer, and Recovery on both BIOS and UEFI production ISOs. Publish only if every required case passes.

Until those runtime artifacts exist, classify Live production userspace as **not accepted** and keep prerelease publication blocked.
