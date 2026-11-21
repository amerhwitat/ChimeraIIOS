# Linux Userspace Gap Audit — ChimeraIIOS / Koronos

**Audit date:** 2026-10-27  
**Status:** engineering gap register; not a claim of Linux compatibility or release readiness.

## Comparison baseline

Linux userspace is not just an init executable. It depends on a stable syscall ABI, process/thread lifecycle, virtual memory, file descriptors and VFS semantics, signals, scheduling, device interfaces, IPC, networking, service supervision, and a working userspace image. A boot banner or ELF loader alone does not satisfy these contracts.

| Area | Linux userspace expectation | ChimeraIIOS evidence / gap | Acceptance required |
|---|---|---|---|
| Process creation | `fork/clone`, `execve`, `wait4/waitpid`, exit/reap and per-process identity | Prior audits found `EXECVE/WAITPID` returning `-ENOSYS`; GETPID hard-coded to 1 and EXIT acknowledgement without teardown were identified on default branch | Parent/child test, exec replacement, exit status and reaping; unique nonzero PIDs |
| Ring-3 execution | Validated executable mapped into user address space, privilege transition, user stack and safe return | ELF segment validation/mapping does not by itself prove a CPL3 transition | Hardware-backed CPL3 entry and user-originated syscall from the same process PID |
| Syscall safety | ABI-defined arguments, user-pointer validation, errno, interruption and lifecycle semantics | Acknowledgement-only syscall paths are not equivalent to implementation | Per-syscall tests, invalid pointer tests, error-path tests, no synthetic success |
| VFS / descriptors | open/read/write/close, path lookup, mount namespaces or equivalent, permissions, descriptor lifetime | RAM-VFS/ISO read tests exist, but target-root publication and process-visible operations require end-to-end proof | Ring-3 OPEN/READ/CLOSE, mount rootfs, writable `/tmp`, permissions and cleanup |
| Init / services | PID 1 supervises services, tracks health, restarts or fails according to policy, shuts down coherently | Service registry and dependency planner are not themselves a running service manager; unverified services must remain BLOCKED | Real service process launch, health check, dependency ordering, failure/rollback and shutdown tests |
| Scheduler / SMP | Runnable work is actually dispatched; APs online and overlapping execution on multiple CPUs | One-CPU/zero-runnable screenshot is not SMP evidence; sequential traces are insufficient | AP startup proof and two pinned workers with measured overlapping execution |
| Device / storage | Drivers expose operational devices and stable storage semantics | Device/storage service states are blocked until real backends prove health | Device I/O tests; installer write, sync, cold reboot and persistence verification |
| IPC / signals | Defined process communication and signal/termination behavior | Must be audited per implemented ABI; do not infer from syscall names | Two-process IPC, signal delivery/masking, interrupted wait and termination tests |
| Networking | Socket API or explicitly documented native equivalent, protocol stack and device path | Linux-compatible networking is not established by the boot path | Loopback plus NIC-backed tests and documented ABI boundary |
| Desktop | Session manager, compositor/display protocol, input, graphics services and app launch | Aurora artwork/boot entry does not prove a live desktop session | Compositor/session health, input event, launch/close app, display recovery |
| Compatibility | Explicit Linux ABI or compatibility layer; otherwise native ABI only | Do not label native Koronos programs Linux-compatible without an implementation | ABI conformance suite or explicit “not supported/not tested” metadata |

## Boot payload contract

For each target `live`, `installer`, and `recovery`:

1. Build the actual production user-init ELF with the kernel's supported ABI and ELF layout.
2. Stage exactly one ELF as a distinct Multiboot2 module named `chimera-user-init-elf target=<target>`; the kernel classifier must map it to `CHIMERA_MODULE_USER_INIT_ELF`.
3. Stage exactly one matching target payload and reject missing, duplicate, ambiguous, or mismatched target modules before ISO mastering.
4. Validate the ELF machine/type, entry point, load segments, bounds, alignment, W^X policy and target metadata before boot.
5. Do not treat shell text emitted by an initramfs script as proof that the separate ELF executed.
6. Emit target readiness only after real CPL3 entry, a user-originated syscall and nonzero PID match, required rootfs/VFS checks, and required services' health postconditions.

## Required regression gates

- [ ] Build script syntax and `git diff --check`.
- [ ] No merge-conflict markers in tracked source.
- [ ] Unit tests for ELF and target/module validation, including missing, duplicate, malformed and mismatched inputs.
- [ ] All six production cases: Live/Installer/Recovery × BIOS/UEFI, bound to the exact candidate ISO SHA-256 and production init ELF SHA-256.
- [ ] Same nonzero PID for user-originated CPL3 syscall acknowledgement and target readiness.
- [ ] Ring-3 OPEN/READ/CLOSE and writable `/tmp`.
- [ ] Real installer write + cold-reboot persistence and real recovery repair postcondition.
- [ ] Aurora session/display health, not just artwork or a boot marker.
- [ ] AP startup and measured overlapping execution on at least two CPUs.

## Linux compatibility statement

Until the ABI, process lifecycle, VFS, IPC, device, networking and runtime tests above pass, describe ChimeraIIOS as a native experimental OS with partial Linux-inspired interfaces—not as a Linux userspace replacement. Do not weaken release gates to make the matrix green.


## systemd comparison: what “services, modules, and targets” actually means

Linux and systemd divide responsibilities across layers:

- **Linux kernel:** processes/threads, virtual memory, scheduler, syscalls, VFS, devices, networking and security primitives. The kernel does not itself implement systemd targets.
- **PID 1 / systemd manager:** parses unit files, builds a dependency graph, schedules jobs, launches processes, tracks exit/health state, restarts according to policy, handles ordering/conflicts, and coordinates shutdown.
- **Units:** `.service` processes, `.socket` activation, `.mount`/ `.automount`, `.device`, `.timer`, `.path`, `.slice`, `.scope`, and `.target` aggregation/synchronization. Kernel modules are generally loaded by userspace tooling (such as `modprobe`) and are not synonymous with systemd service units.
- **Targets:** named synchronization points / groups of units, e.g. `multi-user.target` and `graphical.target`. A target is not an executable and is not “ready” merely because its name was registered.
- **Health and failure:** process exit state and service-specific readiness checks are distinct. `active (exited)` can be valid for oneshot units, but must not be generalized into proof that a long-running daemon is healthy.

Koronos should adopt the same separation of concerns without pretending to implement systemd's full unit compatibility:

1. Kernel primitives must provide real process creation/exec/exit/reap, scheduling, address spaces, syscalls, VFS and device interfaces.
2. A userspace init/service manager owns the service graph and starts real process images. A registry entry is metadata, not a process.
3. Service descriptors should declare stable ID, executable/module path, arguments, dependencies, target membership, criticality, restart policy, readiness probe, shutdown policy and resource/security constraints.
4. The manager validates the full graph (unknown/self/duplicate dependencies and cycles), resolves ordering, starts dependencies before dependents, checks readiness, and rolls back newly started services when a critical dependency fails.
5. Runtime state transitions must be driven by observed process and health events: DECLARED → BLOCKED/STARTING → RUNNING only after successful launch and readiness; then STOPPING/STOPPED, or FAILED/RECOVERING according to policy. Never set RUNNING from registration alone.
6. Targets should aggregate required services and declare explicit postconditions. `live.target`, `installer.target`, `recovery.target`, and `graphical.target` are proposed Koronos concepts, not claims of existing implementation.
7. “Module” must be unambiguous: a Multiboot2 boot module, a loadable kernel module/driver, and a userspace service executable are different object types with separate validation and lifecycles.
8. Add manager tests for dependency order/cycles, launch failures, readiness timeout, unexpected exit/restart budget, shutdown ordering, duplicate instances, and critical-service rollback.

## Proposed Koronos service/target contract (design, not implemented behavior)

- `koronos-init` is the real PID 1 userspace executable; it must execute through the supported user-mode entry path.
- A target manifest binds a target ID to a validated set of service descriptors and required health postconditions.
- A service is READY only when its actual process identity is tracked and its configured readiness check passes.
- A target is READY only when every required service is READY and target-level postconditions pass.
- Logs include monotonic timestamps, target/service IDs, PID, state transition, exit status, restart count and failure reason.
- Missing executable, invalid manifest, cyclic dependency, failed required service, timeout, or missing display/storage capability prevents target readiness and returns a diagnostic failure.
- Service manager unit tests are necessary but insufficient: the release verifier must also observe these transitions in the booted candidate ISO.

This is a design recommendation. The current registry/plan code must not be represented as a complete systemd-equivalent service manager until process launch, health monitoring, restart/shutdown, and target postconditions are implemented and tested.
