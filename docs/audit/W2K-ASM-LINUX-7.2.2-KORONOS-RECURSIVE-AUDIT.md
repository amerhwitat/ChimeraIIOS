# Recursive Koronos kernel source audit — Windows 2000 x86 and Linux v7.2.2

Date: 2026-11-28  
Scope: source-derived design comparison for the x86-64 Koronos kernel. This is an audit and implementation plan, not a claim that the missing subsystems have been implemented.

## Source handling and provenance

- `W2K-ASM.txt - Notepad.pdf` is treated as a reference for architecture and control-flow only. It is Windows 2000-era x86 source/assembly material; do not copy proprietary implementation text or transplant 32-bit assumptions into x86-64 code.
- Linux v7.2.2 is an upstream GPL-2.0 kernel reference. Reuse its documented design concepts, but do not copy GPL implementation into the independently licensed Koronos tree without an explicit licensing decision. Any implementation in Koronos must have clean-room provenance and its own tests.
- Linux source paths below refer to the v7.2.2 tag in the stable Linux repository; the requested Bootlin Elixir endpoint was not directly retrievable during this audit.

## Windows 2000 assembly findings

### Dispatcher and context switching

PDF pages 250 and 254 show `KiSwapThread` selecting the next thread from the processor control block, updating the current-thread pointer, re-queuing the outgoing thread, and calling `SwapContext`. The caller preserves the nonvolatile registers around that call. Page 256 describes `SwapContext` as the routine that transfers processor context and flushes relevant cache/TLB state; the interrupt-dispatch path calls it when a quantum-end decision selected a replacement thread.

Koronos implication: a scheduler must own a stable per-thread saved context and stack, select a distinct runnable thread, switch address spaces where required, and resume the new thread's continuation. Calling a callback synchronously and changing its READY/BLOCKED state after it returns is not equivalent.

### System-service entry and argument validation

PDF pages 417–418 show `KiSystemService` building a trap frame, identifying the service number and caller stack, validating the service-table index, and copying arguments from the caller's stack. Page 474 shows the page-fault path recognizing a fault while copying system-service arguments and converting a user-mode invalid access into an access-violation result.

Koronos implication: syscall dispatch must preserve the complete user register frame, validate the caller's privilege and address space, safely copy arguments, and return through a defined user-mode frame. A syscall acknowledgement is evidence of CPL3 entry, not evidence of a complete syscall ABI or process lifetime.

### Page-fault handling

PDF pages 472–474 show `KiTrap0E` entering with interrupts disabled, capturing CR2 before enabling interrupts, interpreting the page-fault error bits, and calling `MmAccessFault` with the fault address, access direction, previous mode, and trap frame. If the fault cannot be resolved, the path moves into exception handling, including special treatment for faults during syscall argument copying.

Koronos implication: the x86-64 fault path needs a complete saved-register frame, CR2 capture, present/write/user/instruction/reserved-bit decoding, address-space/VMA lookup, demand mapping or copy-on-write resolution, and a process-directed fault/termination path. A page-table builder alone is not a virtual-memory subsystem.

## Linux v7.2.2 source findings

| Source path | Relevant mechanism | Koronos design consequence |
|---|---|---|
| `kernel/sched/core.c` | `__schedule`, local runqueue locking, task selection, `context_switch`, post-switch cleanup | Per-CPU runqueues and a scheduler that switches independently saved task contexts |
| `arch/x86/entry/entry_64.S` | `entry_SYSCALL_64`, `swapgs`, kernel stack selection, saved `pt_regs`, syscall dispatch | Complete privilege transition and kernel-stack/trap-frame discipline |
| `arch/x86/kernel/process_64.c` | `__switch_to`, FPU and FS/GS/TLS state | Context state extends beyond general-purpose registers and RSP |
| `arch/x86/mm/fault.c` | `do_user_addr_fault`, VMA checks, access-error handling, `handle_mm_fault` | Fault resolution is tied to the current task's address space and mapping metadata |
| `mm/memory.c` | `__handle_mm_fault`, page-table allocation and fault resolution | Demand paging needs an explicit VM fault contract and allocation/error handling |
| `fs/namei.c` | `path_lookupat`, `path_openat`, pathname walk and file open | A filesystem needs namespace traversal and open-file objects, not only archive lookup |
| `fs/open.c` | `do_sys_openat2`, open flag validation, descriptor installation | File descriptors and open semantics must be kernel-owned |
| `fs/read_write.c` | `vfs_read`, `vfs_write`, access checks, mode checks, file operations and position handling | Read/write syscalls must route through file objects and filesystem operations |

## Current Koronos source disposition

These are source-level findings, not inferred from a green build:

1. `kernel/core/scheduler.cpp` stores callback tasks and calls the callback to completion in `chimera_sched_run_once`. `chimera_sched_run_parallel` returns zero. It is not the process scheduler described above.
2. `kernel/core/target_launch.cpp` enters one target ELF synchronously through `koronos_arch_enter_user`. When the entry returns or the PIT deadline aborts it, the launcher disarms the timeout, destroys the address space, and marks the process EXITED or FAULTED.
3. `kernel/targets/init_common.h` implements `init_pid1_wait` as an infinite `pause` loop. Its own comment states that this is not a scheduler or child-process supervisor. It can keep the ring-3 image from returning during a short smoke test, but it does not create a resident, schedulable PID 1.
4. `kernel/targets/live_init.c` is a text-console probe and explicitly says no graphical session starts.
5. `kernel/targets/installer_init.c` is a report-only dry run and explicitly says no block device backend is present and no disk will be written.
6. `kernel/targets/recovery_init.c` reports diagnostics and explicitly performs no repair.
7. `koronos.cpp` reports one online scheduler CPU before the AP test. The immutable ISO acceptance artifact reports the AP startup gate failing with `x2APIC unavailable`. The six-case matrix itself runs QEMU with `-smp 1`, so it cannot prove AP concurrency.

## Acceptance-test defect found and corrected

The prior six-case runner waited for kernel-ready, CPL3 syscall, and userspace-ready markers, then waited only two seconds before shutting QEMU down. The target init's bootstrap wait is intentionally longer than two seconds and the kernel PIT deadline is ten seconds. Consequently, the test could terminate QEMU before observing the target's timeout/exit and the verifier could incorrectly report a resident PID 1.

The runner now observes for eleven seconds and fails if QEMU exits during that window. This exceeds the ten-second kernel deadline; the existing verifier rejects the emitted timeout/error marker. This change intentionally makes the current probe payload fail production PID1 acceptance instead of certifying a short-lived readiness handshake.

## Required implementation order

1. **Process-owned context:** PID, parent, state, address-space ownership, kernel stack, saved x86-64 register/trap frame, FPU/SIMD state, FS/GS/TLS state, exit status, and safe reference/lifetime rules.
2. **Real scheduler:** runqueues, locking/interrupt discipline, voluntary and involuntary switches, timer preemption, block/wake, wait/reap, and address-space switching. Keep callback tests separate.
3. **Persistent PID 1:** create PID 1 as a normal schedulable process; transfer control to the scheduler; do not destroy its address space after readiness; fail the target if PID 1 exits unexpectedly.
4. **VM faults:** CR2 capture, error decoding, VMA-like mapping metadata, demand paging, permission checks, and process fault delivery.
5. **VFS:** mount namespace, superblock/inode/dentry/file objects, path lookup, file descriptors, read/write/seek/close, ramfs/tmpfs, and persistent filesystem operations.
6. **Storage and installer:** real block backend, bounded partition/filesystem writes, explicit target selection, durable install, reboot, and readback verification.
7. **Recovery:** read-only discovery, explicit repair plan, safe execution, and independent postcondition tests.
8. **SMP:** APIC discovery, AP startup trampoline, per-CPU stacks and runqueues, TLB shootdown, and concurrent scheduler work. Do not infer scheduler SMP from AP self-test overlap alone.
9. **Desktop acceptance:** actual Live shell/session and Aurora/Marine graphical runtime, not artwork or artifact presence.

## Release rule

Keep readiness probes labelled `production_ready=false`. A successful compile, a successful kernel boot, or a six-case firmware smoke test is not a production release. The same immutable ISO SHA must pass the longer PID1 lifetime test plus independent VFS, installer persistence, recovery repair, AP concurrency, and desktop-runtime checks. Do not weaken these gates to turn the candidate green.
