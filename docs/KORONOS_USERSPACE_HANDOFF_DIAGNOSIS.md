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
