# Current source audit — 2026-11-17 (supersedes older status bullets below)

This update is based on the current `main` source files at the time of review.
It is a source audit, not a fresh kernel build or QEMU runtime result.

## What has advanced since the older diagnosis

The x86-64 path now has more than a placeholder privilege transition:

- `kernel/arch/x86_64/user_entry.asm` installs user selectors, a 64-bit TSS/RSP0,
  configures the SYSCALL MSRs, saves a kernel continuation and CR3, switches to
  the selected address space, and enters ring 3 with `iretq`.
- Its syscall entry saves the user register frame, switches to a dedicated
  kernel syscall stack, dispatches the syscall, and returns to userspace with
  an `iretq` frame. The native exit sentinel restores the saved kernel CR3 and
  original kernel continuation.
- `kernel/core/interrupt.cpp` configures the DPL3 INT 0x80 gate and validates
  the CPU-saved CS RPL before recording the first CPL3-origin syscall.
- `kernel/core/target_launch.cpp` admits the target ELF, invokes the ELF
  address-space loader, sets the active root/PID, enters ring 3 and requires
  the syscall acknowledgement plus a target/PID readiness marker.

These are meaningful x86-64 single-process handoff components. They should not
be described using the older diagnosis that said the TSS, user selectors, ring-3
entry and syscall-origin check were wholly absent.

## What still prevents a production userspace

The decisive limitation remains the lifecycle after entry:

- `process.h` still declares `CHIMERA_PROCESS_LOAD_PLAN_ONLY`; `process.cpp`
  is a metadata/admission table, not an owner of a saved, resumable CPU context,
  kernel stack, parent/child relationship, wait status or address-space lifetime.
- `scheduler.cpp` schedules callbacks. Its callback is run to completion;
  yield/block/exit update callback state but do not switch to another saved
  user register frame. `chimera_sched_run_parallel()` returns zero.
- `target_launch.cpp` calls `koronos_arch_enter_user()` synchronously. When
  the probe exits or the PIT deadline aborts it, the launcher disarms the timer,
  destroys the address space and marks the process exited/faulted. This is a
  bounded one-shot execution, not persistent PID 1.
- The current three target init ELFs are readiness probes. Live does not yet
  provide a production shell/desktop, Installer does not write/install to a
  selected disk, and Recovery does not perform filesystem/boot repairs.
- The initramfs modules are not yet unpacked into a mounted production rootfs
  with VFS-backed filesystems and the required `/dev`, `/proc`, `/sys`, and
  writable `/tmp` semantics.

## Correct Linux reference and implementation order

Linux `init/main.c` separates early kernel initialization from persistent
userspace: `rest_init()` creates PID 1 and `kthreadd`, starts scheduling,
and `kernel_init()` completes initramfs/rootfs setup before executing init.
PID 1 remains a schedulable task. Koronos should follow the architecture, not
copy Linux internals blindly:

1. Replace the callback-only task abstraction for user processes with
   architecture-owned saved interrupt/register frames, kernel stacks,
   address-space ownership, process states and synchronization.
2. Implement a timer/interrupt-safe context switch that can suspend and resume
   a CPL3 process without unwinding the original launcher's C stack.
3. Start PID 1 as a normal schedulable process; keep it alive after readiness.
   Treat PID 1 exit as a target failure.
4. Add initramfs unpacking, rootfs/VFS and process syscalls before claiming a
   general userspace.
5. Implement and test the separate Live, Installer and Recovery behaviors.
6. Add AP startup and real per-CPU scheduling before claiming SMP.

Do not try to fix the lifecycle by removing address-space teardown, increasing
the PIT deadline, faking process states, or relaxing the handoff verifier. Those
changes would mask missing ownership/context-switch semantics.

## Verification boundary

No current-source audit can substitute for the canonical build and fresh
runtime traces. The release gate must still run Live, Installer and Recovery
under BIOS and UEFI from one immutable ISO SHA, require the same nonzero PID
through the CPL3 syscall and readiness events, and independently test desktop
startup, installer persistence, recovery postconditions and real AP overlap.
The readiness-probe manifests must remain `production_ready=false` until those
tests pass with production target implementations.

---

# Koronos userspace handoff: zero process-context diagnosis

## Observed boot output

The runtime report shows all of the following in one boot:

- `[LIVE] Runtime handoff queued`
- `[MON] CPUs: 1`
- seven scheduler task records, with one `RUNNING` and one `READY`
- `[NBIT] Registered process contexts: 0`
- `[USER] Ring-3 Chimera init entered successfully; userspace handoff verified`
- `[INST] Installer target not selected: no installer modules`

These are not equivalent milestones. A scheduler task count is not a process-context count, and printing a Ring-3 message does not prove that an ELF image has been loaded, mapped, assigned a user stack, and entered through a valid privilege transition.

## Source-level finding

The current process interface in `kernel/include/chimera/process.h` defines
`CHIMERA_PROCESS_LOAD_PLAN_ONLY`. The implementation in
`kernel/core/process.cpp` validates ELF metadata and stores a load plan in a
fixed process table. It does not map ELF segments, build page tables, create a
saved CPU context, or perform a Ring-3 transition. Therefore, this API by itself
cannot establish an executable user process.

The scheduler in `kernel/core/scheduler.cpp` stores callback-based scheduler
tasks. Its task records are not process contexts and do not represent ELF CPU
contexts. The current log must not infer process readiness from scheduler task
activity.

## Required code fix

Trace the code that emits the `[USER]`, `[NBIT]`, and `[INST]` lines and
connect the actual init ELF path to the following staged operations:

1. Initialize the process table and record the result.
2. Verify the init ELF image and its program-header table bounds.
3. Admit the ELF and log its PID and segment count; fail closed if admission
   returns an error.
4. Load/map each PT_LOAD segment, zero the BSS tail, and enforce segment
   permissions using the memory manager.
5. Create the user address space, user stack, and architecture-specific saved
   CPU context.
6. Enqueue that context using a process-aware scheduler path and perform the
   architecture's verified privilege transition.
7. Only after a real user-mode entry acknowledgement, report userspace ready.

If the required memory/context-switch facilities do not yet exist for the
target architecture, report `userspace handoff NOT VERIFIED` with the failed
stage. Do not fabricate a process count or convert scheduler tasks into process
contexts just to make the monitor output look healthy.

## Installer status

The installer diagnostic is separate from process admission. Discover and
validate the installer module manifest, select a target only when a matching
module is present, and report a distinct installer-unavailable status otherwise.
A successful init ELF handoff does not imply that installer modules exist.

## Regression acceptance criteria

- Invalid/truncated ELF program-header tables are rejected without out-of-bounds
  reads.
- A missing init ELF or failed admission produces a clear failure stage and a
  non-success handoff status.
- Process count remains zero when no process has been admitted.
- A process is counted as userspace-ready only after address-space and execution
  context setup succeeds.
- Scheduler task count and process-context count are logged separately.
- The `[USER]` success line is absent until the architecture-specific user entry
  path confirms success.
- Installer absence does not masquerade as a kernel or process-loader failure.
- QEMU boot tests verify the actual userspace entry marker, not just successful
  compilation or a queued handoff.

## Current status

This note records a source-level diagnosis and acceptance criteria. It is not a
claim that the missing ELF loader, user address-space setup, or context-switch
path has been implemented or that the ISO has been rebuilt and boot-tested.
The exact log-emitting call site must be located before the success message can
be safely corrected in code.


## Follow-up implementation and acceptance gate (2026-10-18)

- The kernel now explicitly logs that userspace readiness is withheld while the process API is still in load-plan mode. Live and Installer paths report `USERSPACE HANDOFF NOT VERIFIED` instead of implying that a queued handoff is an executing process.
- Multiboot2 module classification now distinguishes the Jasper Recovery initramfs and recovery manifest from Live modules. A host-side regression test covers Live/Recovery/Installer module kinds, and CI compiles it with warnings as errors.
- The GRUB Install menu now routes through Jasper's installer contract checks instead of booting the Live initramfs under an Install label.
- Octavian's full-ISO release workflow requires an explicit `USERSPACE READY: target=live init_pid=` marker. The current kernel does not emit that marker because no verified ring-3 entry acknowledgement is wired up. Consequently, the ISO may be built and retained as a review artifact, but release publication is blocked until the real loader/context-switch path exists and the marker is produced by the executing init process.
- This is deliberately a fail-closed acceptance gate, not a claim that the user process loader has been completed. The next implementation step remains page-table/address-space integration, mapped ELF PT_LOAD segments and BSS, user stack, GDT/TSS and saved context, architecture-controlled ring-3 entry, then a real init process acknowledgement. Installer and Recovery need their own executed userspace/repair tests after that handoff exists.


## Stricter runtime proof contract (2026-10-18)

The host-side verifier now requires three ordered events for the same target and
same nonzero PID:

1. `[KRN ] KORONOS READY`.
2. `USER INIT SYSCALL: target=<target> init_pid=<pid>`, emitted by the syscall
   or exception entry path only after it has established that the originating
   context was at CPL 3. It must not be printed by the pre-transition launch
   code.
3. `USERSPACE READY: target=<target> init_pid=<pid>`, emitted only after init's
   own readiness handshake succeeds.

The stricter verifier and unit tests are an acceptance gate, not proof that the
kernel currently performs the transition. Until the actual architecture entry
path emits the first-user-syscall acknowledgement and QEMU traces pass for each
target, the handoff remains NOT VERIFIED. Never manufacture these markers in a
host test or kernel-side pre-transition code to satisfy CI.


## Architecture source audit — publication gate remains blocked (2026-10-18)

The latest review of the x86-64 source separates acceptance tests from actual execution:

- The ELF loader's callbacks are an interface, not proof that hardware page tables enforce user/supervisor, writable, NX, and W^X permissions.
- Process admission/load-plan metadata does not by itself own a saved CPU context, runnable process, or cleanup-capable address space.
- The current entry/GDT and interrupt path do not establish a complete user-selector + TSS/RSP0 setup, a validated ring-3 return frame, or a syscall path that dispatches a verified CPL-3-originated request.
- A hard-coded GETPID result and an EXIT handler without process teardown are placeholders, not successful process semantics.
- Cooperative callback scheduling is not architecture context switching or genuine SMP.

The latest repository validation is green, but it is not a QEMU proof: https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39126421943

Do not publish a release or report userspace-ready until a freestanding Koronos build and independent QEMU Live, Installer, and Recovery traces prove the real user-mode entry, first syscall, same kernel-owned nonzero PID, readiness handshake, and target behavior. Keep the PR draft while these conditions are unmet.


## Updated source audit and ISO integration fix (2026-11-14)

This section supersedes older statements above where the x86-64 implementation has since advanced. It records source-level findings only; no new ISO or QEMU run is claimed here.

### Linux reference sequence

The current upstream Linux reference is [init/main.c](https://github.com/torvalds/linux/blob/master/init/main.c):

1. rest_init() creates the init task first so it receives PID 1, then creates kthreadd and starts the scheduler.
2. kernel_init() waits for kthreadd, completes kernel initialization, and enters kernel_init_freeable().
3. kernel_init_freeable() prepares SMP and core services, waits for initramfs, opens the initial console when available, and prepares the real root namespace when an early /init is not executable from the initramfs.
4. kernel_init() executes the selected init process (/init first for initramfs, then configured/default init paths). PID 1 remains an ordinary userspace process; it is not a short-lived kernel callback.

Koronos should preserve the same separation: discover/validate boot modules, make a root filesystem available, create a kernel-owned process with an address space and user stack, enter CPL3, and keep PID 1 schedulable while services and the selected target run. A one-shot readiness probe is not a substitute for persistent PID 1.

### Current Koronos source state

- kernel/core/target_launch.cpp now performs target selection, ELF admission, PT_LOAD mapping through the address-space loader, CR3 setup, ring-3 entry, and validates a CPL3-origin syscall plus the target/PID readiness marker.
- kernel/core/process.cpp remains a process admission/state table; the CHIMERA_PROCESS_LOAD_PLAN_ONLY marker remains in the public process header. The bootstrap launcher still enters one user process synchronously and returns to the kernel on exit or its PIT deadline. It is not yet a general process-aware preemptive scheduler with persistent PID 1, child lifecycle, wait/reap, and signals.
- kernel/targets/live_init.c, installer_init.c, and recovery_init.c are explicitly ring-3 readiness probes. They emit the handshake, exercise basic syscalls, and exit. Live is not a graphical desktop, Installer is a storage dry run, and Recovery is diagnostics-only.
- The Multiboot2 initramfs modules are still passed as payload data. The native Koronos path does not yet unpack them into a mounted rootfs with working /dev, /proc, /sys, writable /tmp, and VFS-backed open/read/write/exec.
- The installer still lacks a production block-device writer and persistence verification; Recovery still lacks filesystem/boot repair execution; Aurora still lacks a native compositor/X server session on the freestanding path.

### Comprehensive builder correction

build-chimera-iso.sh previously built the Koronos target-init ELFs through kernel/build-koronos.sh but did not copy them into its own ISO staging tree, even though the GRUB entries referenced /boot/targets/target-init-*.elf. It also did not stage the /boot/ai/knowledge-db.json module referenced by those entries. The builder now:

- copies Live, Installer, and Recovery target-init ELFs to /boot/targets/;
- generates and stages per-target SHA-256/ELF manifests while retaining payload_kind=ring3-readiness-probe and production_ready=false;
- builds and validates the knowledge database in the selected build workspace, then stages it and its checksum under /boot/ai/;
- requires these files during ISO structural verification.

Regression coverage was added to tests/boot/test_iso_target_routing_artwork.py. These changes fix dangling module references in the comprehensive builder's staging path; they do not convert the probe ELFs into production target runtimes or prove a successful BIOS/UEFI boot.

### Remaining acceptance work

1. Implement initramfs unpack/rootfs activation and the minimum VFS/syscall contract needed by the target init.
2. Replace the synchronous probe launcher with persistent PID 1 process scheduling, timer-safe context switching, exit/wait/reap, and signals.
3. Make Live start a real shell/session and Aurora compositor; make Installer perform safe, confirmed disk writes and prove reboot persistence; make Recovery perform and verify real repair operations.
4. Run the unchanged six-case Live/Installer/Recovery × BIOS/UEFI QEMU gate, inspect each trace, and require the same immutable ISO SHA-256 for all cases.
5. Only then treat the native ISO as a release candidate. Packaging success, an ELF header check, or a probe readiness marker alone is insufficient.
