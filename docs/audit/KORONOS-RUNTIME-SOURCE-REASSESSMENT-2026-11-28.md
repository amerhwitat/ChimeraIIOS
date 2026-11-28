# Koronos Runtime Source Reassessment — 2026-11-28

**Purpose:** Correct the previous audit's scheduler disposition after inspecting the complete x86-64 preemption path. This is a source reassessment, not a production acceptance report.

## Repository baseline

- Repository: `amerhwitat/ChimeraIIOS`
- Base: current `main` (observed at `80d27e6b7ed059dba20d23da1dc62d31c66bb864`)
- Prior audit PR #332 was closed unmerged. Its branch was no longer fetchable by branch name when this reassessment began.
- No source code was changed by this reassessment.

## Corrected scheduler finding

The earlier audit was incomplete when it described context switching as wholly absent. Current `main` contains a distinct, one-CPU preemptive kernel-task self-test:

- `kernel/core/preemptive_sched.cpp`
- `kernel/arch/x86_64/context_switch.asm`
- `kernel/arch/x86_64/interrupts.asm`
- `kernel/include/chimera/preemptive_sched.h`
- Boot invocation from `kernel/core/koronos.cpp`

The test constructs initial kernel stacks and saved frames, enters two test tasks, uses PIT IRQ vector 32 and software-yield vector 33, saves/restores the GPR frame and RSP through the assembly interrupt epilogue, and checks timer preemption, alternating task markers, stack guard words and bounded switch counts. This is materially stronger than a callback-only scheduler and is genuine implementation/test code for a single-CPU kernel-thread context-switch path.

### Exact limits of that implementation

It is explicitly isolated from the normal scheduler API:

- `preemptive_sched.h` describes it as a one-CPU preemptive kernel-task runtime kept separate until the assembly and timer gates pass independently.
- The production-facing `chimera_sched_*` implementation in `kernel/core/scheduler.cpp` remains a fixed callback table. `chimera_sched_run_once()` calls the callback synchronously; `chimera_sched_run_parallel()` returns zero.
- `kernel/core/thread.cpp` creates threads by calling `chimera_sched_submit()`, so the public thread API still maps to callback tasks rather than the preemptive context objects.
- The preemption self-test has a fixed four-slot task array and two synthetic kernel tasks. It is not a general process scheduler, does not provide parent/child lifecycle or wait/reap, and is not connected to PID 1.
- The self-test does not establish SMP scheduling, CPU migration, per-CPU run queues, cross-CPU wakeups, or scheduler locking under concurrent CPUs.
- It does not establish user-process context switching between independent address spaces, user fault delivery, TLS/FS/GS state policy, or SIMD/FPU ownership for user tasks.
- The initial frame and assembly path are a specialized kernel-mode test path. It must not be treated as a complete general-purpose thread ABI without separate verification of every entry/exit class and stack invariant.

**Disposition:** one-CPU kernel-task context switching and timer preemption have an implemented self-test path; production scheduler integration, general process lifecycle, user-process scheduling and SMP scheduling remain incomplete. Acceptance must report these gates separately.

## Related source findings

- `kernel/core/process.cpp` admits and tracks ELF process-image metadata and state transitions; it does not itself create a scheduler-owned executable process with saved CPU context, parent/child relations, wait/reap and lifetime-safe teardown.
- `kernel/core/thread.cpp` forwards create/yield/block/exit to the callback scheduler API.
- `kernel/targets/init_common.h` still labels the PID1 helper as a bootstrap idle loop rather than a child-process supervisor.
- `kernel/targets/live_init.c` is a text-console implementation, not a graphical session.
- `kernel/targets/installer_init.c` remains report-only/dry-run and does not write a block device.
- `kernel/targets/recovery_init.c` remains diagnostics-only and does not perform repairs.

## Reference mapping

### User-provided W2K-ASM PDF

The inspected source sections provide behavioral/control-flow comparison points:

- PDF pages 248–261: dispatcher lock release, next-thread selection, ready queues, `KiSwapThread`, `SwapContext`, kernel stack update, process address-space switch and floating-point state considerations.
- PDF pages 417–418: system-service table selection, service-number bounds checks and user argument copying.
- PDF pages 472–474: page-fault entry, capture of CR2 with interrupts disabled, decode of read/write and privilege state, memory-fault resolution, and access-violation handling for faults during syscall argument copying.

These are architectural reference observations only. Do not copy proprietary Windows implementation.

### Linux v7.2.2

The requested Bootlin source URL was not directly retrievable in the prior environment. The exact `v7.2.2` tag source was inspected via the corresponding Linux Git repository. The recorded reference set is:

- `kernel/sched/core.c` — blob `96226707c2f6135341aa779b8262f113e103d8ad`
- `arch/x86/entry/entry_64.S` — blob `253f0a585927fe8b18519dd560eb4e702f8c893d`
- `arch/x86/kernel/process_64.c` — blob `d44afbe005bb512a8d1ad8a904c112559ff8596b`
- `arch/x86/mm/fault.c` — blob `45b99c3b1442d4f18a5179dd1773d76d60342bbb`
- `mm/memory.c` — blob `6b8280cfc1dbea5f370efaeda0f100e2720e523d`
- `fs/namei.c` — blob `19ce43c9a6e662da1a4dcdbc88bcd4ffec6c0c5b`
- `fs/read_write.c` — blob `e8c14e2760b20331ce0aeff15e24cefa2d7df886`
- `Documentation/filesystems/vfs.rst` — blob `7c753148af8883b4c09e5306ee79ef2bd65ebf8c`

Linux is GPL-2.0 licensed. Use these references to understand subsystem contracts and invariants; write original Koronos code and preserve provenance/licensing boundaries.

## Required implementation sequence

1. Promote the verified one-CPU context mechanism into a documented general kernel-thread ABI, with independent test coverage for initial entry, yield, timer preemption, blocking, wakeup, exit and stack reclamation.
2. Integrate it with the public scheduler/thread API; remove the split-brain callback/preemptive scheduling model only after parity tests pass.
3. Add process-owned address-space switching, user return frames, syscall/fault handling and parent/child wait/reap.
4. Implement AP startup and per-CPU scheduler state, reschedule IPIs, safe migration and race-focused SMP tests.
5. Make PID 1 a real supervised process.
6. Complete persistent VFS/storage, safe installer, recovery repair, Live graphical session and each desktop profile.
7. Build one immutable ISO and run the complete BIOS/UEFI and runtime acceptance suite against that exact SHA-256.

## Current build/evidence status

The Structured ISO workflow run `46172162118` was observed in progress on commit `7cfe4551b56329ebad1fccc593c315746fb86e03`. At the last inspection its ISO job had passed setup, tool installation, platform registry validation and target-init routing/release-gate checks; portfolio acquisition was still in progress and the actual boot/ISO test, ISO build and artifact upload steps had not run yet.

That workflow is attached to the now-closed, unmerged audit PR and is not current-main runtime acceptance. No ISO SHA from this run is yet established here. Do not call it a completed build or a runtime pass.

## Fail-closed release matrix

| Gate | Current evidence | Disposition |
|---|---|---|
| One-CPU kernel-thread context switch | Dedicated x86-64 self-test in source; this workflow's result not yet inspected | Implemented test path; runtime result pending |
| General kernel-thread scheduler | Public API still callback-based | Incomplete |
| Process lifecycle / PID 1 supervision | ELF admission metadata and readiness probes only | Incomplete |
| User-process address-space switching | Not established by kernel-task self-test | Incomplete |
| SMP scheduler | AP startup self-test exists separately; no scheduler/AP integration demonstrated | Incomplete |
| VFS/storage durability | No reboot-persistent round trip established | Incomplete |
| Installer | Dry-run/report only | Incomplete |
| Recovery | Diagnostics only | Incomplete |
| Live and desktop sessions | Live text console; desktop runtime not verified | Incomplete |
| Same-SHA complete ISO acceptance | No current-main artifact and full acceptance bundle established | Incomplete |

A skipped, pending, unavailable, or probe-only test is never PASS. Keep the release blocked until every required gate passes on the same immutable ISO artifact.
