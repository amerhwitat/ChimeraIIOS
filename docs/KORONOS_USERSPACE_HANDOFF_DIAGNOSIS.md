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
