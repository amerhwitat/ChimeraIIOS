# Koronos persistent PID 1 and userspace runtime plan

Status: implementation blocker; this document is a plan, not evidence of completion.
Reference model: Linux `init/main.c`, especially `rest_init()`, `kernel_init()`,
`kernel_init_freeable()`, initramfs/rootfs setup, and execution of the selected init.

## Verified source boundary

- `kernel/core/target_launch.cpp` admits and maps one target ELF, switches to its
  address space, enters ring 3 synchronously, waits for a return/deadline, then
  destroys the address space and marks the process exited/faulted.
- `kernel/core/process.cpp` is a process metadata/state table. The public header
  still defines `CHIMERA_PROCESS_LOAD_PLAN_ONLY`.
- `kernel/core/scheduler.cpp` runs callbacks to completion. It does not save/restore
  user register contexts; `chimera_sched_run_parallel()` returns zero until AP
  startup and per-CPU workers are real.
- Current Live, Installer and Recovery init payloads are readiness probes. They
  are not production PID 1, a disk installer, or a repair environment.
- Initramfs modules are currently boot payloads, not a mounted root filesystem
  with a production VFS/syscall surface.

## Required implementation sequence

1. **Process-owned execution context**
   - Define an architecture-neutral process object with PID, parent, state,
     address-space ownership, kernel stack, saved register frame, credentials,
     exit status, and wait/reap lifecycle.
   - Make ELF admission allocate and own the address space and stack atomically;
     unwind all partial allocations on every error.
   - Add explicit process-table locking and PID allocation/reuse rules.

2. **Timer-safe context switching**
   - Implement x86-64 interrupt-frame save/restore and a scheduler switch path.
   - Distinguish callback tasks from process contexts; never reinterpret one as
     the other.
   - Add timer preemption, yield, block, wake, exit, wait and reap semantics.
   - Keep the kernel continuation and per-process kernel stack ownership valid
     across syscall, IRQ and context-switch paths.
   - Add tests for register preservation, CR3 ownership, stack canaries,
     blocked/woken tasks, exit cleanup and invalid transitions.

3. **Persistent PID 1 bootstrap**
   - Reserve PID 1 for the selected target init.
   - Create PID 1 as a normal schedulable process, then start kernel workers
     analogous to Linux `kthreadd`.
   - Enter the scheduler rather than waiting synchronously for init to return.
   - Treat PID 1 exit as a fatal target failure unless an explicit, verified
     replacement-init policy exists.

4. **Root filesystem and syscall contract**
   - Unpack the selected initramfs into a bounded in-memory filesystem.
   - Provide mounted root, `/dev`, `/proc`, `/sys`, writable `/tmp`, file descriptors,
     and real `open/read/write/close/seek` semantics.
   - Add `exec`, `wait`, process identity and error propagation before claiming
     a general userspace.

5. **Three distinct target implementations**
   - Live: init, device discovery, shell/service manager, then compositor/session.
   - Installer: device enumeration, explicit disk selection, partition/filesystem
     creation, installation, bootloader setup, reboot and persistence test.
   - Recovery: read-only discovery first, explicit repair selection, backup/safety
     checks, repair execution and independent postcondition verification.

6. **SMP**
   - Implement firmware/APIC discovery, AP startup trampoline, per-CPU stacks,
     per-CPU scheduler state, TLB shootdown and synchronization.
   - Prove simultaneous execution with per-CPU traces and shared-work correctness;
     QEMU `-smp 2` alone is not evidence.

## Release acceptance

Keep `tests/boot/verify-userspace-handoff.py` fail-closed. For one immutable ISO
SHA, run Live/Installer/Recovery × BIOS/UEFI and require, in each trace:

1. kernel-ready;
2. a CPL3-originated syscall acknowledgement;
3. the same nonzero kernel-assigned PID reporting target readiness;
4. PID 1 remains alive and schedulable after readiness.

Then independently verify Live shell/desktop startup, installer disk writes plus
reboot persistence, Recovery repair plus postcondition, and real AP concurrency.
A probe ELF must remain labelled `production_ready=false` and must never be
promoted to production by changing a manifest or test.

## Build and artifact integration

The canonical `./build-chimera-iso.sh --clean-state --storage-auto` path must
build target init ELFs from source, emit target manifests with hashes and payload
roles, stage the exact binaries referenced by Jasper/GRUB, and reject stale or
missing artifacts. CI must exercise that canonical builder, not only
`boot/iso/build-iso.sh`. Publish only after the full release matrix and target
postconditions pass.
