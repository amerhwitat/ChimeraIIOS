# Koronos Native Runtime: Recursive Source Audit and Acceptance Plan

**Status:** audit baseline only; production release remains blocked.
**Baseline:** `main` at `80d27e6b7ed059dba20d23da1dc62d31c66bb864` (2026-11-26).
**Integration branch:** `work/koronos-native-runtime-integration-20261128`, created from that exact main head.
**Scope:** clean-room x86-64 kernel, userspace, Live/Installer/Recovery and desktop runtime; evidence-driven ISO acceptance.

## 1. Source provenance and method

This audit uses two requested references as design/behavioral references:

1. The user-provided `W2K-ASM.txt - Notepad.pdf`. The relevant inspected excerpts are PDF pages 248-261 (dispatcher unlock, ready-thread selection, `KiSwapThread`, `SwapContext` call path and thread selection), pages 417-418 (`KiSystemService`: service-table selection, bounds validation, argument copying from user stack, service dispatch), and pages 472-474 (`KiTrap0E`: capture CR2 with interrupts disabled, decode read/write fault, pass previous mode and trap frame to memory manager, distinguish recoverable faults from access violations). These pages are evidence of the reference's control-flow contracts, not permission to copy proprietary implementation.
2. The requested Linux v7.2.2 source tree, retrieved by exact tag from `gregkh/linux` because the Bootlin URL was not directly fetchable in this environment. Retrieved source files and blob IDs:
   - `kernel/sched/core.c`: `96226707c2f6135341aa779b8262f113e103d8ad`
   - `arch/x86/entry/entry_64.S`: `253f0a585927fe8b18519dd560eb4e702f8c893d`
   - `arch/x86/kernel/process_64.c`: `d44afbe005bb512a8d1ad8a904c112559ff8596b`
   - `arch/x86/mm/fault.c`: `45b99c3b1442d4f18a5179dd1773d76d60342bbb`
   - `mm/memory.c`: `6b8280cfc1dbea5f370efaeda0f100e2720e523d`
   - `fs/namei.c`: `19ce43c9a6e662da1a4dcdbc88bcd4ffec6c0c5b`
   - `fs/read_write.c`: `e8c14e2760b20331ce0aeff15e24cefa2d7df886`
   - `Documentation/filesystems/vfs.rst`: `7c753148af8883b4c09e5306ee79ef2bd65ebf8c`

Linux files are GPL-2.0 licensed. Do not transplant their implementation into this GPL-3.0 ChimeraIIOS tree without a deliberate licensing/provenance decision. Use them to understand contracts, invariants, and architecture boundaries; write original Koronos implementation and tests.

## 2. Repository ancestry decision

The previously proposed branch `feat/koronos-process-owned-runtime-2026-11-02` exists, but its comparison against current `main` is `diverged`: 209 commits ahead and 545 behind, with merge base `1694f610d5809b09e7247865be51ee0a335d18b1`. It is not a safe direct integration base. This branch is therefore created from the current `main` head; candidate changes from the old branch must be reviewed and ported selectively, not merged wholesale.

## 3. Current-main source audit

The following observations were made directly against current `main`:

- `kernel/core/scheduler.cpp` maintains a fixed task table, ready-state selection and callback function pointers. Its task selection bookkeeping is not by itself a resumable CPU context. A callback that is called synchronously is not a process/thread context switch.
- `kernel/core/target_launch.cpp` loads a target ELF and enters user code through the current user-entry path. The launch path tracks an active PID/address-space and recognizes a user readiness marker, but it is not yet evidence of a scheduler-owned process lifetime with independent saved register/stack state and a full wait/reap lifecycle.
- `kernel/targets/init_common.h` explicitly describes `init_pid1_wait()` as a bootstrap idle loop, not a scheduler or child-process supervisor. A resident pause loop is not a functioning PID 1 service manager.
- `kernel/targets/live_init.c` explicitly identifies itself as a text console, not a graphical desktop.
- `kernel/targets/installer_init.c` explicitly says no block device is written and the path is report-only/dry-run.
- `kernel/targets/recovery_init.c` explicitly says it performs diagnostics and repairs nothing.

These source comments and implementations define real gaps. Do not turn these states into PASS by changing labels, accepting kernel-written markers, or relaxing release gates.

## 4. Implementation work packages

### A. Process and scheduler core
- Define stable task/thread objects with kernel stack, saved callee-saved state, interrupt/trap frame, address-space reference, PID/TID, parent/child links, state, affinity, exit status and reference-counted lifetime.
- Implement x86-64 assembly save/restore with a documented ABI and a first-run trampoline. Preserve callee-saved registers, stack pointer, flags/interrupt discipline, FS/GS/TLS state as applicable, FPU/SSE state policy, and address-space/TLB ownership.
- Implement run queues, per-CPU current/idle thread, ready/block/wake transitions, timer tick accounting, reschedule requests, interrupt-return scheduling and lock ordering.
- Implement wait/reap and safe teardown only after a task is no longer executing on any CPU. Test preemption, yield, blocking, wakeup, exit and repeated reuse.
- SMP acceptance must show AP startup, per-CPU initialization, independent run queues or a proven shared-queue design, inter-CPU wakeup/IPI, affinity, race-safe task migration and measured overlapping execution.

### B. Syscall and exception boundary
- Specify one canonical syscall ABI and document the Linux-compat translation separately from internal semantic syscall IDs.
- Validate syscall number/table bounds and copy user arguments through fault-safe accessors; never trust user pointers or lengths.
- Save a complete trap frame and verify user/kernel origin from saved privilege state.
- Page faults must capture CR2 before enabling interrupts, decode present/write/user/reserved/instruction-fetch bits, resolve only valid mappings, enforce permissions, and deliver deterministic user faults without corrupting kernel state.
- Add negative tests for invalid syscall numbers, unmapped pointers, read-only writes, user/kernel boundary crossing, malformed ELF segments and faults during argument copying.

### C. Address spaces, memory and ELF
- Complete physical-frame ownership, page-table allocation/free, user/kernel mapping separation, stack guard pages, ELF segment permissions, zero-fill/BSS, relocations if supported, and TLB invalidation/shootdown.
- Tie address-space lifetime to process references; never free the current or remotely active address space.
- Prove user isolation with two concurrent processes attempting forbidden reads/writes.

### D. VFS and persistent storage
- Implement explicit vnode/inode/dentry/file abstractions, mount table, path traversal, descriptor table, permissions, open/read/write/seek/close, directory enumeration, and error semantics.
- Add a real block-device driver/backend, partition discovery and filesystem implementation with flush/barrier handling and crash-safe metadata updates.
- Test create/write/fsync/close/reboot/open/read, partial I/O, ENOSPC, read-only mounts, corruption detection and no-format-by-default behavior.

### E. PID 1, Live, Installer and Recovery
- PID 1 must be a scheduler-owned resident process that spawns, supervises, reaps and restarts or reports failed services.
- Live must mount a read-only system image with writable RAM overlays where appropriate and start an actual graphical session/compositor, input and applications.
- Installer must require explicit target-disk confirmation, expose a dry-run plan, write partition/filesystem/bootloader data only after confirmation, verify writes, install a root filesystem and prove reboot into that root.
- Recovery must mount safely, diagnose and repair supported faults, preserve user data, and verify a concrete postcondition. No silent formatting or destructive default.
- If no persistent disk is available, Live/Installer/Recovery must have explicitly bounded RAM fallback behavior and clearly report that persistence/install is unavailable.

### F. Desktop sessions
- Integrate compositor, graphics backend, display modes, input devices, window management, shell/session startup, fonts, icons and core apps.
- Validate Aurora Glass, Marine Blue, FreeXP and FreeWin11 as real sessions rather than catalogue entries or screenshots. Record the display backend, resolution, input and application launch evidence.

## 5. Acceptance matrix (release-blocking)

| Gate | Required proof | Current disposition |
|---|---|---|
| Kernel boot | immutable ISO boots to kernel-ready on supported BIOS and UEFI configurations | Not revalidated on this branch |
| Context switch | two independent threads resume from saved contexts; timer preemption demonstrated | Incomplete |
| Process lifecycle | PID 1 spawns, blocks/wakes, waits/reaps child; no use-after-free | Incomplete |
| CPL3 syscalls | user-originated syscalls, argument validation, return-to-user and fault isolation | Probe-level evidence only; production contract incomplete |
| SMP | APs online and overlapping work measured on multiple CPUs | Incomplete |
| VFS/storage | durable file round-trip across reboot on same installed root | Incomplete |
| Installer | explicit safe install, verified writes and reboot persistence | Dry-run only |
| Recovery | real repair and verified postcondition | Diagnostics only |
| Live desktop | native graphical session with input and launched applications | Text console only |
| Other desktops | each supported session boots and passes its own runtime checks | Unverified |
| Release artifact | same ISO SHA passes full acceptance; logs and artifact retained | No current-head evidence |

## 6. Plan / Do / Check / Act loop

1. **Plan:** select one work package, state invariants and acceptance tests before implementation.
2. **Do:** implement the smallest end-to-end vertical slice on this integration branch, with unit and integration tests.
3. **Check:** build from a clean checkout; run static/unit/boot/runtime tests; capture full logs, workflow run IDs and SHA-256 of the exact ISO.
4. **Act:** fix the root cause, not the assertion; rerun focused tests and the full regression matrix. A skipped, unavailable or probe-only test is never PASS.
5. Repeat until every release gate above passes on the same immutable artifact. Only then prepare production acceptance metadata and release review.

## 7. Environment and evidence limits

This commit is an audit/plan artifact, not a kernel implementation or a successful build. No ISO was built or booted during this audit. Prior environment checks reported no local project checkout, no QEMU/NASM/x86-64 cross compiler, and insufficient local disk space on `/mnt/c`; recheck those constraints before attempting a local build. GitHub workflow runs from older commits are historical evidence only and must not be attributed to this branch or current `main`.

## 8. Immediate next engineering slice

Start with the scheduler-owned x86-64 thread context and deterministic two-thread switch test, then connect timer preemption and process lifetime. This is the dependency root for a real PID 1 and service supervision. Do not start by promoting current init payloads or by modifying acceptance wording.


## 9. Historical ISO evidence reviewed on 2026-11-28

An available prior artifact bundle, `chimera-immutable-iso-firmware-acceptance.zip`, contains six QEMU cases (Live, Installer and Recovery under BIOS and UEFI) for ISO SHA-256:

`4de3011b2231cf106ac2241ecd4494ce4f93521b05a8c39a065ad1058550f639`

Its summary records all six cases as PASS, with QEMU exit code 0, kernel-ready, init-syscall and userspace-ready flags. However, the recorded QEMU command for every case uses `-smp 1`; the verifier checks the target-specific user-originated init syscall/readiness handshake. This is useful historical firmware/boot/handoff evidence, but it does not exercise AP startup or concurrent execution, independent thread contexts, timer preemption, child process supervision, VFS durability, installer disk writes/reboot persistence, recovery repair, or graphical desktop startup.

The bundle must not be relabelled as a production acceptance result. In particular, the current source implementations still explicitly report Installer dry-run/no block-device writes, Recovery diagnostics-only, and Live text-console-only. The artifact's PASS statuses are scoped to the checks actually performed and do not override these source facts.

A separate prior Koronos/Octavian candidate artifact records a different ISO SHA (`3b01fa899ac8ef66b7faee94e27adab7956356606cb6d36ffb3938ae78d49d9e`) and `all_pass: false`, with all six target/firmware cases failing to complete the expected kernel-ready / user-init syscall / userspace-ready sequence. These are distinct artifacts and must not be conflated.

## 10. PR-head CI triggered by this audit baseline

The PR-head commit `f5e0e5db9b710c9c45c60a925aaaf68a00a5fec4` automatically triggered:
- Structured ISO workflow run `46171980282` (run 11198), job `iso` (`141062209358`).
- Desktop Compatibility CI run `46171980336` (run 16864), job `portable` (`141062209328`).
- Chimera CI/CD run `46171980225` (run 9236), with infrastructure validation and code-generation jobs completed successfully; Windows build and overall workflow were still in progress at the time of inspection.
- GitHub Pages deployment and WSL drive-alias validation completed successfully.

At inspection time, the structured ISO, desktop compatibility and Chimera CI/CD workflows were still in progress. Their success is not assumed. Even if the ISO workflow produces a new artifact, its test scope must be read from the job logs and result JSON before assigning acceptance status. A documentation-only PR trigger is not itself proof of a source implementation change.

## 11. Next implementation order and stop conditions

The next source change must be the smallest verifiable scheduler vertical slice: a documented x86-64 context ABI, assembly save/restore, first-run thread trampoline, two independently resumable kernel threads, and deterministic switch tests. Only after that passes should timer interrupt preemption, blocking/wakeup, process wait/reap and PID 1 supervision be layered on. SMP then requires real AP bring-up and cross-CPU reschedule signaling; VFS/storage and target init work depend on stable process/address-space ownership.

Do not add placeholder APIs that are never called, turn the existing callback scheduler into a production claim, or mark a gate passed because a test emitted a marker. If a safe source patch cannot be built and run against the target architecture, keep it unmerged and report the precise missing proof.
