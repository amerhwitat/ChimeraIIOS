# Process lifecycle root-cause review — 2026-10-23

## Source-level finding

Reviewed the current branch implementations of:

- `kernel/core/process.cpp`
- `kernel/include/chimera/process.h`
- `kernel/core/target_launch.cpp`
- `kernel/userspace/native_init.c`
- `kernel/core/syscall.cpp`

The production service startup failure is not just a missing service manifest or readiness marker. The process subsystem exposes ELF admission, lookup, and state-setting APIs. It does not expose a parent/child model, a spawn/exec operation that can launch a second process, a wait/reap operation, exit-status delivery to a parent, or an operational scheduler handoff for child processes. The target launch path admits one init image, loads it, enters ring 3 synchronously, then closes its VFS descriptors, destroys its address space, and records the process as exited/faulted. It has no child-process supervision loop.

Native init then explicitly runs its VFS self-test and exits with status 78 after printing `NATIVE INIT BLOCKED`. That behavior is correctly fail-closed, but it makes operational Live/Aurora, Installer, and Recovery services impossible to claim as started.

The compatibility syscall dispatcher is not a substitute for the native process-bound syscall path: its GETPID and EXIT handling explicitly rejects requests because it lacks an active process identity and teardown context.

## Required implementation contract

Before native init may report service health, implement and test all of the following as one coherent process lifecycle:

1. Kernel-owned process identity with parent PID, lifecycle state, exit status, and generation-safe PID allocation.
2. A spawn/exec operation that validates ELF segments, constructs process-owned page tables and user stack, initializes descriptors, and registers a runnable child.
3. A scheduler path that can run child processes without synchronously nesting an unbounded ring-3 call inside target launch.
4. Wait semantics with a defined blocking/nonblocking policy and correct wakeups when a child exits.
5. Reap semantics that only release terminal children and reclaim address spaces, descriptors, mappings, and process slots exactly once.
6. User-pointer validation for every process-control syscall and race-safe state transitions.
7. Regression tests for invalid ELF, PID exhaustion/reuse, parent-child ownership, child exit status, wait wakeup, double reap, descriptor cleanup, address-space cleanup, and target isolation.
8. A userspace service supervisor that spawns the actual target service, performs a real health probe, handles exit/restart policy, and only then emits target readiness.

Do not implement spawn as a wrapper around the current synchronous `koronos_arch_enter_user` call; that would not provide a working supervisor and can make a parent unable to supervise a running child.

## Adjacent blockers

- Installer still requires a writable storage-backed root namespace and cold-reboot readback.
- Rootfs and tmpfs syscalls must be observed from ring 3 in production traces.
- The current candidate smoke workflow reconstructs target-specific ISOs; it is not the actual production ISO × six firmware/target matrix.
- Aurora health, recovery repair postcondition, and AP-backed overlapping execution remain separate acceptance gates.
- The closeout collector intentionally emits NOT RUN for those gates. The generated report must continue to fail DAPS until actual raw production traces are supplied.

## Status

This is a source-level root-cause finding and implementation contract, not a claim that the process lifecycle has already been implemented or that any production boot has passed. Keep release blocked until code, tests, and actual production runtime evidence agree.
