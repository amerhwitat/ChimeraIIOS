# Koronos targets, services and native userspace runtime gap

## Scope and naming

This document separates three boot paths that must not be conflated:

1. **Linux live editions** use a Linux kernel, initramfs, and the distribution's real PID 1/service manager. OctavianOS's Debian live image uses systemd and currently selects `multi-user.target`; Aurora is started by the live-session launcher.
2. **Native Koronos** starts the Koronos ELF through the Multiboot2 handoff. It does not become a systemd system merely because it has similarly named targets or service records.
3. **Installer and Recovery candidates** may contain Linux/BusyBox initramfs payloads. Their presence in an ISO is not proof that Koronos can execute them as native processes.

## Linux reference model

Use the upstream systemd boot model as the behavioral reference, not as code to copy blindly:

- The initramfs has its own `initrd.target`; the root device and filesystems are prepared before the transition to the real root.
- The host service manager activates the dependency closure of `default.target`.
- `sysinit.target` and `basic.target` provide synchronization points; `multi-user.target` is the non-graphical system target; `graphical.target` pulls in multi-user and adds the graphical login/session stack.
- `rescue.target` and `emergency.target` are separate degraded boot modes.
- Requirement edges (`Wants=`, `Requires=`, `Conflicts=`) and ordering edges (`Before=`, `After=`) are orthogonal. Independent units can start concurrently; ordering must be explicit.
- A target is a synchronization/aggregation point, not a claim that every optional service succeeded.

References:
- https://freedesktop.org/software/systemd/man/latest/bootup.html
- https://freedesktop.org/software/systemd/man/latest/systemd.special.html
- https://freedesktop.org/software/systemd/man/latest/init.html
- https://docs.kernel.org/admin-guide/initrd.html

## Koronos target graph to implement

| Koronos target | Linux analogue | Required postcondition |
|---|---|---|
| `koronos.initrd.target` | `initrd.target` | Boot modules bounded/validated; initramfs unpacked; early console and device discovery ready |
| `koronos.rootfs.target` | `initrd-root-fs.target` | Selected root mounted; VFS root switched transactionally; rollback remains possible |
| `koronos.sysinit.target` | `sysinit.target` | Memory, clocks, device graph, logging, entropy and core filesystem services initialized |
| `koronos.basic.target` | `basic.target` | Process manager, IPC, local mounts, temporary filesystems and required sockets active |
| `koronos.multi-user.target` | `multi-user.target` | Console/login, networking and enabled system services active |
| `aurora.target` | `graphical.target` | Display server/compositor and desktop session report independent health |
| `koronos.rescue.target` | `rescue.target` | Minimal authenticated/diagnostic shell; no automatic disk writes |
| `koronos.emergency.target` | `emergency.target` | Minimal recovery console when normal root/service initialization fails |
| `koronos.installer.target` | installer-specific target | Native installer ELF running; device topology and disk/ESP selection verified; transaction and persistence checks enabled |
| `koronos.recovery.target` | recovery-specific target | Read-only discovery first; repair only after explicit device selection and postcondition verification |

## Unit/service contract

A native service unit needs, at minimum:

- Stable unit identity, executable/module identity, version/hash and target membership.
- Explicit `Wants`, `Requires`, `Before`, `After`, `Conflicts` and `OnFailure` edges.
- A job state machine (queued, waiting, starting, running, succeeded, failed, timed out, stopping, stopped).
- A process-owned PID/address space, kernel stack/context, exit status, wait/reap and signal/stop path.
- Start/stop deadlines, bounded restart policy, dependency failure propagation and durable diagnostics.
- Parallel job execution only when the dependency graph allows it and the scheduler can actually run work concurrently.
- A target reaches its success state only after its required services satisfy their postconditions; optional service failures remain visible.

## Current Koronos implementation boundary

The current mainline code is not yet a native target/service runtime:

- `kernel/core/process_loader.cpp` validates and maps ET_EXEC segments through supplied callbacks; its header explicitly says it prepares an image but does not switch to ring 3.
- `kernel/core/interrupt.cpp` installs DPL0 gates and currently ignores the interrupt frame.
- `kernel/core/syscall.cpp` rejects process-dependent GETPID and EXIT because it has no trusted caller identity/lifecycle hook.
- `kernel/core/scheduler.cpp` intentionally returns zero from `chimera_sched_run_parallel()`; callback dispatch is not a process context switch.
- Native init therefore remains fail-closed (exit 78) when the required filesystem/process/device/graphics services are not available.

An older experimental branch contains a candidate single-process user-entry path, but it is substantially diverged from current mainline and is not safe to merge as a wholesale runtime replacement. It must be selectively ported, reconciled with current memory/process APIs, and tested at exact-head BIOS and UEFI boots.

## Required implementation order

1. One canonical build-root contract for kernel, bootloader, initramfs, installer, recovery and ISO outputs (implemented in the accompanying build changes).
2. Real physical-frame ownership and page-table/address-space creation with shared supervisor mappings.
3. Process-owned kernel stacks and initial saved user context; validated ELF mappings and rollback.
4. Per-CPU identity, TSS.RSP0/GS ownership, syscall entry/return and trusted PID lookup.
5. Process exit/wait/reap, scheduler-stack handoff and deferred address-space destruction.
6. Initramfs extraction/VFS mount, file syscalls and a real native init ELF for each target.
7. Declarative unit dependency graph, target job queue, failure/timeout/restart semantics and actual parallel dispatch.
8. Target-specific BIOS/UEFI cold-boot acceptance for Live, Installer and Recovery using the same immutable ISO hash.

Do not weaken the fail-closed gates, promote smoke-test ELFs to production init, or report target readiness from module presence, shell startup, kernel idle-loop markers or build completion alone.
