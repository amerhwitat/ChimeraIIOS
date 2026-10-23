# Koronos cross-OS syscall, interrupt, and API compatibility audit

**Audit date:** 2026-10-23  
**Scope:** ChimeraIIOS/Koronos x86-64 branch `fix/stage-production-init-elf-modules-20261020`  
**Status:** Audit and remediation specification; not a claim of implementation or production acceptance.

## Executive finding

Koronos currently has a small native semantic syscall ABI, an x86-64 IDT/ISR scaffold, and a compatibility recognizer/translator. It does **not** implement all Linux syscalls, Windows Kernel32/Win32 APIs, or macOS/XNU syscalls. A recognizer, constant, manifest entry, stub, or successful compile is not an implementation. Unsupported operations must return a documented error and must never claim success.

The right architecture is a stable Koronos kernel ABI plus separate user-space compatibility layers:
- Linux: ELF/ABI loader, Linux syscall-number tables by architecture/ABI, Linux errno and structure layouts, signal/thread semantics, VFS, VM and process semantics.
- Windows: PE/COFF loader and Win32 user-space DLL layer (Kernel32/KernelBase/API-set forwards), backed by an NTDLL/native boundary and kernel object/process/thread/VM/I/O primitives where needed. Kernel32 is **not** the Windows kernel and its public Win32 API surface is not equivalent to a syscall table.
- macOS: Mach traps/ports and BSD syscall ABI are distinct surfaces. XNU's BSD syscall master table is a generated source of truth for that table, not a complete inventory of all macOS APIs. User-space libSystem/framework APIs also need their own compatibility implementations.

## Source snapshot: native Koronos ABI

Observed in `kernel/include/chimera/syscall.h`:
- ABI version: 1; maximum argument count: 6.
- Semantic IDs declared: EXIT, GETPID, YIELD, TIME_TICKS, READ, WRITE, MMAP, MUNMAP, IOCTL, NANOSLEEP, WAIT, ARCH_PRCTL, EXIT_GROUP, OPEN, CLOSE, SEEK.
- The existence of an enum entry does not prove a dispatch implementation exists.

Observed in `kernel/core/syscall.cpp` native ring-3 dispatcher:
- Implemented cases visible in the audited switch: GETPID, YIELD (currently a no-op in the bootstrap single-process path), TIME_TICKS, OPEN, READ, WRITE, CLOSE, SEEK, EXIT, EXIT_GROUP.
- MMAP, MUNMAP, IOCTL, NANOSLEEP, WAIT, and ARCH_PRCTL are declared but have no cases in that switch and therefore fall through to the unsupported error path.
- The separate compatibility dispatcher intentionally rejects GETPID and EXIT/EXIT_GROUP because it lacks a bound process context. Do not conflate that dispatcher with the native process-bound path.
- Pointer-taking operations must validate the complete user range, permissions, overflow, and address-space ownership before copying or touching memory. Returning an error for an invalid pointer is required; dereferencing arbitrary user pointers in kernel mode is not.

Observed in `kernel/include/chimera/interrupt.h` and `kernel/core/interrupt.cpp`:
- The public header defines 256 IDT entries, IRQ base 32, INT 0x80, Windows legacy INT 0x2E, and DOS INT 0x21.
- `interrupts.asm` provides vector stubs; that does not mean all exception/IRQ/device semantics are implemented.
- An INT vector being recognized is not equivalent to implementing the associated OS ABI. INT 0x2E is not a universal substitute for modern Windows x64 SYSCALL. INT 0x21 is a DOS interrupt convention and must only be enabled in a defined DOS/VM compatibility environment.
- Review and test the exception error-code frame, privilege transition, GS/TSS/RSP0 handling, interrupt acknowledgement/EOI, PIC/APIC routing, per-CPU state, reentrancy, and safe return paths. A handler must not report a user-originated syscall acknowledgement without checking the actual saved privilege state and active process context.

Observed in `kernel/core/target_launch.cpp` and `kernel/userspace/native_init.c`:
- Installer target launch explicitly fails closed when the storage-backed root namespace is not mounted.
- Native init currently exits with a blocked status when its required runtime services are unavailable rather than supervising a complete target.
- These are production blockers independent of syscall naming or API catalog size.

## Cross-kernel comparison

| Dimension | Koronos audited snapshot | Linux kernel | Windows | macOS / XNU |
|---|---|---|---|---|
| Primary syscall model | Small semantic ABI; partial dispatch | Architecture-specific syscall tables and generated metadata; broad process, VM, VFS, signal, IPC, networking and device APIs | User-mode Win32 APIs route through Kernel32/KernelBase/API sets and NTDLL; native system-service boundary is separate | BSD syscall table plus Mach traps and IPC/ports; user-space libSystem/frameworks form additional layers |
| Process lifecycle | Initial ELF admission and single-process bootstrap path; full scheduler-owned lifecycle unproven | fork/clone/exec/wait, credentials, signals, threads, namespaces and cgroups | Process/thread/object model with handles, access checks, waitable objects and loader/runtime contracts | BSD process/thread semantics plus Mach tasks/threads/ports |
| Virtual memory | ELF mappings exist; native MMAP/MUNMAP dispatch missing in audited switch | mmap/mprotect/munmap, page faults, VMAs, accounting and protection | VirtualAlloc/VirtualProtect/section mappings through Win32/native memory manager | mmap/mprotect/munmap plus Mach VM interfaces |
| Files / I/O | Partial root VFS operations; storage-backed installer root missing | VFS, file descriptors, mount namespace, poll/epoll, sockets, block and character devices | Win32 handles, object manager, I/O manager, IRPs and completion semantics | BSD file descriptors/VFS plus Mach and IOKit interfaces |
| Interrupt / entry | IDT and stubs exist; complete per-device and APIC behavior must be proven | Architecture-specific entry/exit code, IRQ domains/controllers, softirqs/workqueues and driver frameworks | IDT/APIC/ISR/DPC/IRQL model with strict kernel-driver contracts | XNU interrupt/driver subsystems and Mach/BSD boundaries |
| Compatibility strategy | Recognizer + semantic translation scaffold | Native Linux ABI; compat ABIs are explicit and architecture-scoped | Reimplement documented Win32 user-space API and required native semantics; do not copy private syscall numbers | Explicit BSD ABI plus Mach traps; public API compatibility above these boundaries |

## Required implementation layers

1. **ABI registry and generated tables**
   - Keep stable Koronos semantic IDs separate from foreign syscall numbers.
   - Record OS, architecture, bitness, entry mechanism, number, name, argument schema, pointer directions, structure version, error convention, implementation status and tests.
   - Generate tables from reviewed machine-readable sources; reject duplicate number/name mappings and unknown ABI combinations.
   - Pin source revisions and licenses. Never scrape undocumented private numbers and treat them as stable contracts.

2. **Safe syscall boundary**
   - One process-bound dispatcher with validated syscall origin, process identity and address-space identity.
   - Checked copy-in/copy-out helpers; no raw user pointer dereferences.
   - Standard negative errno internally and explicit per-ABI conversion at the boundary.
   - Unknown/unimplemented calls return ENOSYS; invalid arguments/pointers return appropriate errors; never return fake success.
   - Define cancellation, restart, blocking, signals, timeouts and process-exit semantics before adding wait/nanosleep.

3. **Foundational kernel services before broad API coverage**
   - Scheduler-integrated process/thread creation, context switch, blocking/wakeup, wait/reap, cancellation and robust exit teardown.
   - VM mapping/protection/unmapping, page-fault handling, user-copy, memory accounting and W^X/NX enforcement.
   - VFS descriptors, open flags, seek, metadata, directory iteration, pipes, poll/select and socket foundations.
   - Timer/time APIs, signals or a deliberate signal-equivalent design, synchronization primitives, credentials/security, IPC and device abstractions.
   - Interrupt controller support, IRQ registration/EOI, APIC/IOAPIC, per-CPU state, SMP-safe locking and timer delivery.

4. **Windows compatibility**
   - Implement documented Win32 APIs in user-space DLLs with tests and versioned behavior.
   - Build the PE loader, imports/exports, relocations, TLS, exception/unwind handling, calling conventions, handles, waitables, synchronization, file/console, virtual memory, process/thread and loader APIs.
   - Keep Kernel32/KernelBase/NTDLL boundaries explicit. Do not call an API “implemented” because an export stub exists.
   - Start with a bounded, named API subset and return documented errors for unsupported functions. Full Windows compatibility is a multi-year compatibility project, not a kernel syscall patch.

5. **Linux compatibility**
   - Define the initial supported ABI precisely (x86-64 LP64 first; do not imply i386/x32 support).
   - Add per-ABI syscall tables and generated conformance tests. Implement foundational calls in dependency order: exit/getpid, read/write/openat/close/lseek, mmap/munmap/mprotect, brk, clock/time, futex, clone/execve/wait, signal actions/return, stat-family, pipes/poll and sockets.
   - Respect Linux structure layouts, flags, restart/error semantics and per-call versioning. Do not map a Linux number directly to a Koronos number without a validated translator.

6. **macOS compatibility**
   - Treat Mach traps and BSD syscalls as separate ABI families.
   - Define supported CPU/ABI and binary format explicitly; x86-64 macOS and Apple Silicon are not interchangeable.
   - Implement only documented/required libSystem APIs and BSD calls needed by a named workload. Mach ports, task/thread calls, VM calls, launch/runtime conventions and code-signing expectations require their own design.
   - Do not equate the XNU BSD syscall master table with all macOS framework APIs.

## Check / Plan / Do / Act loop

### CHECK
- Run native unit tests for each syscall ID, unknown IDs, bad pointers, range overflow, read-only destinations, wrong PID/CR3, and return-value/errno conversion.
- Run IDT tests for all 256 installed gates, exception vectors with/without hardware error codes, CPL3 INT 0x80, supervisor-only vectors, timer IRQ and EOI, nested/reentrant cases, and SMP/per-CPU state.
- Verify every API export has an implementation status and tests; an export list alone is not acceptance.
- Run the full build, static checks, host tests, QEMU tests and production ISO boot tests separately.

### PLAN
- Prioritize the production-critical path: ring-3 entry and syscall acknowledgement → safe VFS/syscall boundary → supervised Live/Recovery services → installer storage namespace → display/Aurora and recovery flows → AP-backed SMP.
- In parallel, establish one supported Linux x86-64 ABI slice. Defer full Windows/macOS coverage until the underlying process, VM, VFS, IPC and loader primitives are operational.
- Track each API as `implemented`, `partial`, `stubbed`, `unsupported`, or `not tested`; only tested behavior may be marked implemented.

### DO
- Implement each dependency slice with unit tests and fault-injection coverage.
- Never weaken DAPS or generate synthetic production traces.
- Add real boot evidence with the exact ISO SHA-256 and preserve raw serial/debug logs and artifact provenance.
- Keep compatibility layers out of the kernel when user-space emulation is the correct boundary.

### ACT / release gate
- Run the existing `tools/production-closeout-daps.py` unchanged against the real collected evidence.
- Require all six Live/Installer/Recovery × BIOS/UEFI cases, matching positive kernel-owned syscall/readiness PIDs, rootfs and writable tmpfs evidence, display/Aurora evidence, installer cold-reboot persistence, recovery postcondition, and independent AP-backed concurrency evidence.
- If any evidence is missing, stale, mismatched, candidate-only, or unverifiable, release remains blocked.

## Primary references

- Linux, adding a syscall (official kernel docs): https://docs.kernel.org/process/adding-syscalls.html
- Linux, entry/exit for exceptions, interrupts and syscalls (official kernel docs): https://docs.kernel.org/next/core-api/entry.html
- Microsoft, Nt and Zw native service routines: https://learn.microsoft.com/en-us/windows-hardware/drivers/kernel/using-nt-and-zw-versions-of-the-native-system-services-routines
- Microsoft, warning that internal Windows APIs are unstable and public APIs should be preferred: https://learn.microsoft.com/en-us/windows/win32/devnotes/calling-internal-apis
- Apple XNU BSD syscall master table (source of generated BSD syscall metadata): https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/syscalls.master
- OSDev IDT technical reference (secondary, architecture reference): https://wiki.osdev.org/IDT
- OSDev ISR entry/return reference (secondary, architecture reference): https://wiki.osdev.org/Interrupt_Service_Routines

## Release status

**BLOCKED.** This document is an audit and implementation roadmap, not evidence that missing syscalls, interrupts, Win32 APIs, macOS APIs, service supervision, installer persistence, Aurora handoff, or SMP have been implemented. The six-case production gate remains mandatory.
