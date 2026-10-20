# Koronos service lifecycle parity audit — 2026-10-20

## Scope and evidence boundary

This is a source comparison against the current upstream Linux kernel tree and its documented subsystem contracts. It is not a claim of Linux ABI or feature parity. The shared kernel source is maintained in ChimeraIIOS and vendored into OctavianOS; the service manager changes must remain byte-for-byte equivalent in those paths.

## Linux counterparts and implementation status

| Concern | Linux counterpart | Koronos status in this change |
|---|---|---|
| Boot-to-init ordering | `init/main.c`: `rest_init()`, `kernel_init()`, init selection and error handling | Kernel service callbacks now have explicit ordered startup; target-specific user init is still a separate path and must be staged/executed. |
| Executable loading | `fs/exec.c`, `fs/binfmt_elf.c`, `kernel_execve()` | ELF loading/ring-3 smoke exists; a complete VFS/path lookup/exec model and script interpreter are not supplied by this service manager. |
| Service dependency ordering | Linux generally delegates long-running userspace service units to init systems such as systemd; this is not a kernel service-manager API | Koronos adds a bounded 64-entry dependency DAG, cycle rejection, dependency gating, explicit start/health/stop callbacks and reverse-order shutdown. |
| Health and restart policy | Userspace init/service manager policy; Linux kernel does not mark arbitrary services running on registration | A service becomes RUNNING only after start and health callbacks succeed; optional one-time restart is bounded; failures block dependants. |
| Process identity and exit | `kernel/fork.c`, `kernel/exit.c`, `kernel/sched/`, syscall implementations | Still requires real process-owned syscall context, PID, wait/exit/reaping and scheduler integration. Do not interpret this callback manager as process supervision. |
| Filesystem and storage | `fs/`, `block/`, `drivers/` | Real VFS/mount, block I/O, persistent storage, installer media access and rootfs lifecycle remain separate implementation tasks. |
| Device discovery and drivers | `drivers/base/`, `drivers/pci/`, storage and display drivers | Inventory/probe is not equivalent to a bound, operational driver. Hardware-specific start and health callbacks still need implementations. |
| SMP and synchronization | `kernel/sched/core.c`, `kernel/smp.c`, locking primitives | Lifecycle calls are explicitly serialized for now. A kernel-wide lock and AP-started concurrent execution are not implemented by this patch. |
| Graphical session | DRM/KMS, input and userspace compositor/session manager | Aurora's real session launch, framebuffer/device access, input and compositor health remain unverified. |
| Installer and recovery | Linux userspace tools plus filesystem/block/device interfaces | Real disk transaction/reboot and repair operations are not implemented by this lifecycle abstraction. |

## Lifecycle contract introduced

The boot path now registers and health-checks the initialized console, module registry, scheduler, hardware inventory, driver manager, process registry, and logging adapters. These states describe only the kernel bootstrap facilities actually checked; they do not claim that storage, network, security, display composition, or a graphical session is running.

- Manifest validation rejects missing IDs, duplicate IDs, missing dependency references, invalid restart policies and over-capacity graphs.
- Topological resolution rejects dependency cycles.
- Callbacks execute in dependency order. A failed dependency becomes BLOCKED and cannot start its dependants.
- RUNNING is recorded only after both start and health callbacks return success.
- `CHM_RESTART_FAILURE` permits exactly one bounded retry.
- Shutdown visits the resolved plan in reverse order.
- Critical failures abort the startup pass; noncritical failures remain visible and block dependants.
- Calls are serialized by the caller because no global service-manager lock exists yet.

## Required next integrations

1. Add concrete timer, memory-management, storage/block, filesystem/mount, input, display/compositor, network, security, and session service backends with real start/health/stop callbacks; only existing bootstrap facilities are wired today.
2. Implement native target init programs that call those services through supported interfaces; no readiness-only ELF is acceptable.
3. Give Live, Installer and Recovery distinct dependency manifests and real operations.
4. Add process-owned syscall dispatch, wait/exit/reap, user-memory validation, and safe cross-process lifecycle.
5. Add AP startup and a real SMP lock around shared service state before concurrent service calls.
6. Run the canonical build and the full six-case production BIOS/UEFI matrix, then independently verify Aurora, installation/reboot, and recovery repair.

## Sources

- Linux boot/init source: https://github.com/torvalds/linux/blob/master/init/main.c
- Linux scheduler documentation: https://www.kernel.org/doc/html/latest/scheduler/
- Linux subsystem API documentation (memory, drivers, storage, filesystems, networking): https://docs.kernel.org/subsystem-apis.html

No Linux implementation source is copied into Koronos here. The parity comparison is behavioral and architectural; kernel-internal Linux APIs are not a stable userspace ABI and are not directly portable to Koronos.


## Follow-up hardening — 2026-10-20

The lifecycle validator now rejects empty service IDs, invalid initial state values, self-dependencies and duplicate dependency entries. Startup/shutdown returns an error if the bounded global state registry cannot record a required transition, instead of silently proceeding with incomplete state. Matching regression cases are present in both repositories.

The current manager is deliberately serialized: its global state registry has no SMP lock. Do not call it concurrently from APs or independent service workers until a real kernel synchronization primitive is integrated. The ID state table also assumes service ID storage remains valid for the lifetime of registered states; production manifests should use static-lifetime IDs until ownership is redesigned.

## Current acceptance state

The latest source commits are on open draft PRs. A fresh workflow run for the newest commits has not been returned by the available run query, so compile/test status remains **unverified**. Production acceptance is still blocked. The current kernel startup has real flags for console, module scan, scheduler, device inventory, driver probe/start, and process-registry initialization, but these do not provide the missing filesystem/VFS, native script interpreter, complete process execution and lifecycle, storage/network/security/display session services, or target operations.
