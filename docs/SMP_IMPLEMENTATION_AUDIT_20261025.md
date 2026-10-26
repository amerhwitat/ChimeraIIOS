# SMP implementation audit (2026-10-25)

## Decision

**Real SMP: NOT IMPLEMENTED / NOT VERIFIED. Release gate: BLOCKED.**

This audit is against the ChimeraIIOS branch `fix/uefi-native-syscall-ack-20261024`. It is a source audit, not a hardware test. It does not claim an AP has started, that an APIC IPI has been delivered, or that two tasks have executed concurrently.

## Source findings

- `kernel/core/scheduler.cpp`: `chimera_sched_run_parallel(first_cpu, n)` deliberately returns zero. `chimera_sched_run_serial_range` calls `chimera_sched_run_once` in a loop and is explicitly cooperative/serial.
- `kernel/include/chimera/scheduler.h`: the public contract says parallel execution returns zero until architecture AP startup and independent per-CPU workers exist.
- `kernel/arch/x86_64/entry.asm`: the Multiboot2 bootstrap establishes one bootstrap stack, identity-mapped page tables, a GDT, and enters `koronos_boot`. The inspected entry has no secondary-processor trampoline or AP handoff path.
- `kernel/arch/x86_64/interrupts.asm`: generates a shared ISR table; vector 32 routes to the timer handler. The inspected file does not contain a local-APIC EOI path, ICR/SIPI startup sequence, or per-CPU interrupt stack selection.
- `kernel/core/interrupt.cpp`: `chimera_interrupt_init()` builds one static IDT and loads it with `lidt`; `chimera_interrupt_enable()` executes `sti`. The inspected implementation does not initialize a local APIC or establish per-CPU IDT/TSS state.
- `kernel/CMakeLists.txt`: the Koronos x86-64 build is delegated to `kernel/build-koronos.sh`; this source audit did not run that build.

These findings are intentionally scoped to the inspected source paths. A future discovery of another platform implementation must be reviewed and wired explicitly; it must not be inferred from CPU counts, scheduler API parameters, or unrelated architecture files.

## Required implementation sequence

### 1. Discovery and platform contract

1. Parse Multiboot2 information tags and/or ACPI RSDP → XSDT/RSDT → MADT using bounded, overflow-checked physical-memory reads.
2. Validate table signatures, lengths, checksums, enabled/online-capable local APIC entries, duplicate APIC IDs, address overrides, and the BSP APIC ID. Reject malformed tables without dereferencing untrusted physical addresses.
3. Separate `discovered`, `startup_requested`, `online`, and `failed` CPU states. Never derive `online` from a configured CPU count.
4. Detect and explicitly gate xAPIC/x2APIC mode. Do not write xAPIC MMIO registers if the platform is in an incompatible mode or the MMIO mapping is absent.

### 2. AP startup

1. Reserve a page-aligned, identity-addressable trampoline below 1 MiB and verify its physical address is representable by the SIPI vector. Ensure the page is not overwritten by the loader or kernel.
2. Define and test a versioned trampoline data block containing the target CR3, long-mode entry, APIC ID, per-CPU stack, and per-CPU state pointer. Validate every address and required mapping before sending an IPI.
3. Establish GDT, long-mode paging, stack, GS/per-CPU base, IDT/TSS policy, and a C ABI-aligned entry on each AP. Keep interrupts disabled until local state and interrupt-controller routing are valid.
4. Send INIT/SIPI according to the selected APIC mode and platform requirements; bound every wait with a monotonic timeout. Check ICR delivery status where supported.
5. Require an atomic AP-online acknowledgement written by the AP only after it has installed its own required state and entered its own worker loop. A timeout marks that AP failed and cannot be converted to success.

### 3. Per-CPU execution and synchronization

1. Give each online CPU its own current-task slot, idle path, stack, scheduler entry, and interrupt/TSS state. The BSP must not call AP worker functions on behalf of APs.
2. Protect global run-queue and task-state transitions with well-defined locks/atomics. Document lock ordering; never hold a global scheduler lock while invoking a task callback, filesystem/backend callback, or waiting for another CPU.
3. Enforce affinity against discovered-and-online CPU IDs, not merely an integer range. Reject empty/out-of-range/unavailable masks and handle an affinity change while a task is running without duplicate ownership.
4. Implement cross-CPU wakeup only after an IPI delivery and acknowledgement contract exists. Keep interrupt handlers bounded; defer scheduling decisions to a safe interrupt-return or explicit scheduler boundary.
5. Define task teardown, migration, and CPU-offline behavior so a task cannot be concurrently owned by two CPUs or freed while another CPU is executing it.

### 4. Parallel proof

The acceptance test must fail unless all conditions are true:

- Two distinct APIC IDs are observed in `online` state from AP-written acknowledgements.
- Two distinct CPU-bound tasks are pinned to separate online CPU IDs and each reports its own task ID and CPU identity from inside its execution callback.
- A shared monotonic clock records `start` and `end` events. The intervals overlap: `A.start < B.end && B.start < A.end`.
- Both tasks make progress while intervals overlap; neither trace is synthesized by the BSP or emitted by a serial harness.
- Repeated runs pass under QEMU with at least two vCPUs and, where available, physical hardware. Logs include source commit, machine configuration, APIC IDs, time source, and ISO SHA-256.

### 5. Negative tests and release binding

Test missing MADT, malformed lengths/checksums, duplicate IDs, AP timeout, rejected IPI, duplicate startup, absent APIC, x2APIC mismatch, unavailable affinity CPU, empty affinity mask, task wakeup races, lock contention, and AP failure during teardown. Every failure must remain explicit and must not increase the online count.

Bind the complete trace and test results to the exact immutable ISO SHA-256. Production closeout also requires all six Live/Installer/Recovery × BIOS/UEFI userspace handoff cases, CPL3 syscall and file-I/O evidence from the real init PID, installer write/cold-reboot persistence, and a verified recovery repair postcondition. Passing source-contract tests, a kernel build, or a boot smoke test is insufficient.

## Current outcome

No AP trampoline, APIC initialization, per-CPU scheduler worker, or overlap test is claimed as implemented by this audit. The existing fail-closed return in `chimera_sched_run_parallel()` must remain until the platform startup and concurrency contracts above are implemented and tested. Do not merge or publish a production artifact while this gate is blocked.
