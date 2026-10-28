# Koronos cross-platform kernel and userspace compatibility matrix

Status: design and acceptance contract; this document does **not** claim that the listed facilities are implemented.

## Scope and compatibility model

The goal is to run native Chimera/Koronos applications first, then provide explicitly versioned compatibility layers for selected Linux, Windows, and macOS user-space ABIs. Compatibility is per architecture, ABI version, feature, and executable format. It is not a promise to run every binary or driver from those operating systems.

Do not copy proprietary Windows/macOS implementation code, private interfaces, SDK contents, or restricted binaries into this repository. Use documented public specifications, clean-room implementations, and redistributable test fixtures.

## Boot and firmware boundary

| Layer | Required contract | Evidence required |
|---|---|---|
| BIOS boot | Valid boot image and documented loader handoff; firmware calls only during boot where applicable | QEMU/OVMF-independent BIOS boot trace and memory-map checks |
| UEFI boot | PE/COFF EFI loader, memory map, GOP/console selection, ACPI tables, ExitBootServices sequencing | OVMF trace showing successful handoff, no post-exit boot-service calls |
| Boot ABI | Versioned boot context; validated pointers, lengths, physical ranges and memory map | Malformed-context tests and hash-bound boot artifacts |
| Runtime firmware | Separate UEFI runtime-service capability with virtual-address transition and synchronization, or explicitly unsupported | Per-service tests; never treat boot services as runtime services |

## Kernel architecture and hardware abstraction

Required architecture-owned interfaces:

- CPU feature discovery and policy (feature presence is not proof of initialization).
- Per-CPU state, GDT, TSS/RSP0, IDT, IST stacks and interrupt-controller setup.
- Uniform trap frame for exceptions, IRQs, syscalls and context-switch continuation.
- Resumable context switching that preserves the ABI-required registers and flags, kernel stack, FPU/SIMD state policy, address-space root and task ownership.
- Physical-frame allocator, virtual-memory manager, page permissions, user/kernel separation, safe user-copy and page-fault containment.
- APIC/IOAPIC or supported interrupt controller, timer source, AP startup, per-CPU scheduler state and synchronization.
- ACPI table validation and explicit device enumeration; no assumption that a reported logical CPU is online.

Every architecture implementation must document register/frame layout, selector values, stack alignment, interrupt enable/disable rules, CR3/PCID policy if used, TLB invalidation, and ownership/lifetime rules.

## Process and executable runtime

The process runtime must provide real, tested transitions—not admission metadata alone:

1. Validate ELF64/Mach-O/PE headers and all offsets, lengths, arithmetic, alignment and segment overlaps before mutation.
2. Construct a fresh address space transactionally; map PT_LOAD or format-specific segments with correct permissions and W^X policy, copy file bytes, zero BSS, validate executable entry, and build the user stack.
3. Bind a task control block, kernel stack, trap frame, address space and descriptor table.
4. Implement create/exec, exit, block, wake, wait, reap, fault containment and complete resource reclamation.
5. Preserve process identity through syscall entry and return. Do not synthesize PID, return success for unimplemented operations, or report readiness from kernel-authored markers.

## System-call compatibility

Keep a stable, documented native semantic syscall ABI. Each foreign ABI is a separate adapter:

| ABI family | Required adapter behavior |
|---|---|
| Linux | Architecture-specific syscall numbers/register convention, errno translation, signal/thread/process semantics, file descriptors, virtual memory, polling, clocks, futex/thread primitives and documented ioctl subsets |
| Windows | Documented Win32/NT user-mode API subsets, PE/COFF loading, handles/object semantics, virtual memory, synchronization, threads, exception behavior and subsystem/library strategy |
| macOS | Mach-O loading, documented POSIX layer plus selected Mach/BSD interfaces, task/port semantics, memory mappings, signals/threads, dyld/shared-cache and framework policy |

These are not interchangeable tables. Keep source ABI identity (OS, architecture, entry mechanism, bitness and version) separate from the canonical operation. Unknown calls must fail with the correct ABI-specific error. An operation may be advertised as supported only when its semantics, error paths and resource lifetime are implemented and tested.

### Syscall entry requirements

- Validate the saved privilege level and caller context at the architecture entry boundary.
- Validate every user range with overflow-safe arithmetic and copy data through fault-safe kernel helpers; never dereference a user pointer directly.
- Validate descriptor/handle ownership and access mode; cap lengths and prevent integer truncation.
- Preserve required registers and return state; define interrupt/preemption policy and signal/exception interactions.
- Test invalid pointers, wraparound, short reads/writes, interrupted waits, cancellation, invalid descriptors, concurrent close/use and process exit races.

## Interrupts, exceptions and drivers

- Distinguish CPU exceptions, external IRQs, IPIs and syscall entry.
- Define interrupt acknowledgement, masking, nesting, EOI, deferred work, spurious interrupts and per-CPU routing.
- Establish recoverable user faults and fatal kernel-fault policy with diagnostic evidence.
- Use a documented driver model and capability boundaries. Do not load Linux kernel modules, Windows kernel drivers or macOS kexts as though they shared an ABI.
- Start with explicit paravirtualized/virtio and emulated device support; each driver must prove DMA bounds, queue ownership, interrupt handling, reset and failure recovery.

## VFS, storage and userspace

- A single VFS contract with mount namespaces/permissions and separately implemented filesystem drivers.
- Writable tmpfs must be mounted through the actual VFS; syscall open/read/write/seek/close must operate on process-owned descriptors and validated user buffers.
- Implement service management, persistent PID 1 supervision, child reaping, dependency health checks and structured failure reporting.
- Target readiness must be derived from observed service/session postconditions, not a fixed delay or log string.
- Installer acceptance must prove write plus cold-reboot persistence; recovery must prove a repair postcondition; desktop acceptance must prove compositor/session and input progress.

## SMP acceptance

A CPU is online only after its AP startup path has reached a defined per-CPU ready state. A configured CPU count or incremented counter is not proof. Test concurrent execution using per-CPU observations and overlapping critical sections, with synchronization that is valid on the target architecture. Exercise affinity, wakeups, timer interrupts, IPI delivery, lock contention and CPU failure/timeouts.

## Release gates

Keep the production verifier and exit-78 safeguard fail-closed. Release requires:

- All six Live/Installer/Recovery × BIOS/UEFI production cases.
- Each trace bound to one immutable candidate ISO SHA-256 and exact production-init ELF SHA-256.
- Genuine CPL3 user-originated syscall acknowledgement and target readiness with the same nonzero PID and required ordering.
- Real VFS read/write evidence, service health, target-specific postconditions, and no fabricated markers or test-ELF substitution.
- Separate evidence for AP startup and overlapping execution on at least two CPUs.
- Reproducible build logs, artifact hashes, regression tests and explicit unsupported-feature reporting.

A source contract, isolated probe, successful compile, kernel-ready marker, or serial scheduler test is useful evidence but does not substitute for end-to-end production acceptance.

## Implementation order

1. Architecture trap/context ABI, TSS/IDT/IST, per-task kernel stacks and address-space switching.
2. Transactional executable loader and real process lifecycle.
3. Safe user-copy and VFS-backed descriptors/tmpfs.
4. Process-bound syscalls and persistent service supervision.
5. AP startup and genuine SMP scheduling.
6. Boot-mode matrix, target postconditions and unchanged six-case production verifier.
7. Add compatibility adapters incrementally, each with ABI-specific conformance suites; do not claim complete Linux/Windows/macOS compatibility without a defined compatibility profile and test corpus.
