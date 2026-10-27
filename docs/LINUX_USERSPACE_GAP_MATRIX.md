# Linux userspace parity gap matrix

**Scope:** native Koronos userspace in ChimeraIIOS and the vendored Koronos userspace in OctavianOS, compared with the Linux userspace boot/runtime contract. This is an engineering gap inventory, not a claim of Linux ABI compatibility or production acceptance.

## Linux baseline

A Linux boot does not stop at loading an ELF. The kernel establishes memory/address-space and privilege-transition state, mounts an initramfs root, executes PID 1, provides a process-aware syscall boundary and file descriptor/VFS APIs, and lets init supervise services. The distribution supplies additional userland components (dynamic linker, libc, shell, utilities, service manager, device management, logging, networking, and desktop stack).

## Current state and gaps

| Area | Linux behavior | ChimeraIIOS evidence/state | Required implementation / acceptance |
|---|---|---|---|
| Boot payload | Kernel consumes initramfs and executes its /init as PID 1 | Multiboot2 module scanner classifies init ELF and Live/Recovery payloads; classification alone is not extraction or execution | Verify target-specific module identity/hash; bounded CPIO-newc extraction; reject traversal, duplicate paths, malformed headers and truncated archives |
| Root filesystem/VFS | Initramfs entries are published as a root mount; mount namespace and VFS mediate path lookup | Existing build/initramfs code does not prove a production root was published through a kernel VFS | Implement archive-to-VFS publication using the real mount ABI; verify /, /init, /dev, /proc, /tmp; fail closed on partial mount |
| ELF/process | execve maps PT_LOAD, BSS, stack/auxv, permissions, then enters user mode | ELF admission and callback-based load planning exist; they are not equivalent to scheduled ring-3 execution | Connect address-space mapper, context/trampoline, TSS/RSP0, per-process CR3, guarded user stack, scheduler and cleanup |
| Syscalls | Syscalls operate on the calling task and validate user pointers | Compatibility semantic dispatcher had fabricated PID 1 and acknowledged exit without teardown; this commit changes those cases to ENOSYS | Route native syscall entry to active process context; validate user memory; implement real PID, read/write, mmap/munmap, wait, exit/exit_group |
| Process lifecycle | fork/clone, exec, wait/reap, signals and exit status have defined semantics | Process records exist, but process records alone do not provide runnable contexts or parent/child lifecycle | Add context-owned task/process association, child creation, exit/reap, wait queues, signals and fault cleanup; test races and stale PID/handle reuse |
| Scheduling | Preemptive task scheduling, block/wake, timers and SMP coordination | Cooperative callback scheduler exists; parallel dispatch deliberately returns zero until real AP workers exist | Architecture context switch, timer preemption, blocking syscalls, wake queues, per-CPU current task and independently running AP workers |
| File descriptors | Per-process fd table, open/read/write/close/dup/pipe, permissions and error semantics | No demonstrated process-owned descriptor table backed by production VFS | Implement fd lifetime/reference counts, VFS operations, permission checks, pipe/IPC and negative tests |
| Device and pseudo filesystems | devtmpfs/devices, procfs, sysfs, tmpfs and block-backed filesystems | Service bootstrap explicitly leaves device/storage services declared, not running | Register real device backends; mount proc/sys/dev/tmp; prove writable tmpfs and read-only boot media; then persistent storage |
| Service supervision | PID 1 starts dependencies, tracks exits, restarts configured services and exposes status/logs | Dependency ordering and service state registry exist, but registry/bootstrap do not launch or health-check services | A real init/service manager with start/stop/restart, dependency failure propagation, logs, health checks and target completion |
| Runtime/toolchain | ELF interpreter, libc, shell, core utilities, package/runtime metadata | BusyBox-based initramfs exists as diagnostic environment; native ABI completeness is not established | Define native libc/sysroot and syscall ABI; package production shell/utilities; test real applications without host fallbacks |
| Observability | procfs task/memory stats, logs, tracing, resource accounting | Scheduler snapshots and host-side tools exist; no proven kernel-backed procfs/task telemetry | Publish kernel-owned process/memory/cpu data; make ps/top/TaskMon consume that API, not fabricated/static data |
| GUI | Session manager, graphics/input/audio device interfaces and compositor | Aurora/Marine assets and launch routing exist; a running desktop is not established by assets | Start session from real init; validate display/input services, compositor health, app launch and clean shutdown |
| Installer/recovery | Target-specific userspace, storage writes, transaction/repair postconditions | Target payloads/routing are present but not full install/repair acceptance | Six BIOS/UEFI target runs; install + cold reboot persistence; recovery action with verified postcondition |
| Security | Credentials/capabilities, syscall pointer validation, mount policy, W^X and isolation | Some ELF bounds/W^X checks exist; full end-to-end isolation remains unproven | Audit every syscall and VFS boundary; capability/credential policy; negative tests and isolation tests |

## Immediate implementation order

1. Rootfs archive extraction and actual VFS root publication.
2. Kernel-owned process context connected to ELF loader, ring-3 entry and syscall entry.
3. Real PID/exit/wait semantics and fd/VFS syscall path.
4. Runnable init/service manager and health-checked Live/Installer/Recovery targets.
5. procfs/task telemetry and shell utilities backed by kernel data.
6. Real AP startup/context switching before claiming SMP.
7. Aurora/Marine, installer persistence and recovery postcondition tests.

## Release evidence

The production gate remains fail-closed. Required evidence is a native build and unit tests, real CPIO-to-VFS tests, ring-3 init syscall acknowledgement followed by readiness from the same nonzero PID, and six separate Live/Installer/Recovery × BIOS/UEFI traces against the unchanged verifier. Follow with Aurora startup, installer cold-reboot persistence, recovery repair postcondition and overlapping execution on at least two CPUs. Source inspection or a passing contract test is not runtime acceptance.

## Linux source mapping

Use Linux as a behavioral reference, not as code to copy wholesale: initramfs and rootfs handling (init/initramfs.c, fs/), process creation and exit (kernel/fork.c, kernel/exit.c), syscall entry and dispatch (arch/x86/entry/, kernel/sys.c), scheduler (kernel/sched/), and procfs (fs/proc/). Exact Linux APIs and source paths vary by kernel release and architecture.
