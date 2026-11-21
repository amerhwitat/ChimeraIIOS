# Koronos runtime parity: Linux and Windows

Status: cross-OS design and evidence matrix. This document records gaps, not a claim of runtime parity. It applies to ChimeraIIOS Koronos and its integration into OctavianOS.

## Comparison matrix

| Area | Linux reference contract | Windows reference contract | Current Koronos/Chimera evidence | Required implementation and proof |
|---|---|---|---|---|
| Process and threads | Tasks, scheduler/context switching, exit/wait/reap, signals | Process/thread objects, dispatcher, waitable objects | ELF admission, PID/state records and bootstrap launch exist; full scheduler-owned lifecycle is unproven. | Real context switches, blocking/wakeup, parent-child exit status, wait/reap, cancellation, cleanup and concurrent task tests. |
| Address spaces and faults | Per-process mappings, page faults, user-copy checks, mmap/munmap | Private virtual address spaces, memory manager, sections and paging | Loader/page-table pieces and range checks exist; process-switch and fault-containment evidence is incomplete. | Prove CR3/address-space switch, mapped/unmapped user buffer behavior, recoverable faults, guard pages and teardown. |
| Syscalls and libraries | Linux syscall ABI plus libc-facing behavior | NT system services and Win32 APIs through subsystem boundaries | Native syscall coverage remains narrow; source registries do not establish complete ABI compatibility. | Specify Koronos native ABI; implement validated syscall contracts and native libc/sysroot. Keep unsupported calls fail-closed. Build executable tests. |
| Filesystem and I/O | VFS, mounts, file descriptors, offsets, filesystem and device operations | I/O manager, handles/object model and layered IRP driver routing | ISO9660/RAM-VFS and device source exist, but production root mount and process-owned fd I/O are not proven end-to-end. | Bounded CPIO extraction into mounted VFS; /dev, /proc and writable /tmp; real process-owned OPEN/READ/WRITE/CLOSE with permissions, offsets and invalid-pointer tests. |
| Executable compatibility | ELF loader, Linux ABI, dynamic loader and runtime libraries | PE/COFF loader, imports/relocations, Win32/NT API contracts | ELF admission exists; PE inspection/loader and compatibility registry exist but are not proof of broad Windows app support. | Test malformed/valid ELF and PE, relocations/imports, entry/stack, W^X, missing imports and teardown. Publish exact supported profiles and APIs. |
| Security | Credentials, permissions, capabilities/LSM hooks, namespaces and resource limits | Access tokens, object ACLs, handle rights and security reference monitor | ELF W^X and user-range checks are partial controls; complete per-process credentials/handles are not established. | Enforce access/ownership at every object boundary; test cross-process isolation, privilege denial and resource limits. |
| Service manager | PID 1 plus long-running supervised services and health checks | Service Control Manager and service processes with status/control contracts | Target markers and service registries do not prove a persistent supervisor. | Start real services, track dependencies, restart/failure behavior and reap children; prove healthy Aurora/Marine process and display/input path. |
| Desktop | Real display/input/compositor and application processes | Windowing/graphics subsystem and user-mode services/apps | Aurora/Marine artwork, panels and target definitions exist, but assets are not session health. | Verify actual frames, input events, app launch/shutdown, and session health emitted by the real process. |
| Installer/recovery | Durable storage operations and meaningful repair tools | Storage/filesystem stack and recovery environment | Target boot smoke is not persistence or recovery proof. | Write to disposable install disk and verify after cold reboot; seed a recovery fault, repair it and assert postcondition. |
| SMP | AP startup, per-CPU state, preemption, scheduler and synchronization | Multiprocessor scheduler, interrupts and dispatcher/synchronization objects | Prior parallel reporting was serial; no acceptable overlapping multi-CPU proof yet. | Boot at least two APs; log distinct CPU IDs and overlapping execution intervals; stress locks, wakeups and per-CPU state. |

## Current acceptance blockers

- The OctavianOS PR #135 independent production-userspace verifier failed for Live, Installer and Recovery because the traces lacked the user-originated CPL3 init syscall acknowledgement and actual init PID readiness marker.
- The six-case candidate ring-3 smoke is explicitly not production payload acceptance. Some UEFI smoke logs also reported missing matching OVMF code/vars images.
- The required six production cases are Live/Installer/Recovery × BIOS/UEFI, each tied to an immutable candidate ISO SHA-256 and the exact production init ELF hash.
- Installer cold-reboot persistence, recovery repair postcondition, Aurora/Marine session health and AP-backed SMP remain separate mandatory gates.

## Priorities

1. Fix production init identity and the genuine CPL3 syscall/actual PID trace; do not synthesize markers or weaken the verifier.
2. Mount the extracted rootfs in the real VFS before launch and implement per-process file descriptors and ring-3 OPEN/READ/WRITE/CLOSE.
3. Implement scheduler-owned context switching, process exit/wait/reap and fault cleanup.
4. Add a persistent supervisor with service health checks and real Aurora/Marine sessions.
5. Verify installer persistence and recovery repair on disposable media.
6. Implement documented native ABI/libc, then separately test supported Linux and Windows compatibility subsets.
7. Prove AP startup and overlapping execution on at least two CPUs.
8. Keep release fail-closed until all six immutable-ISO production traces and all postconditions pass.

## References

- Linux VFS: https://github.com/torvalds/linux/blob/master/Documentation/filesystems/vfs.rst
- Windows user/kernel isolation: https://learn.microsoft.com/windows-hardware/drivers/gettingstarted/user-mode-and-kernel-mode
- Windows virtual address spaces: https://learn.microsoft.com/en-us/windows-hardware/drivers/gettingstarted/virtual-address-spaces
- Windows I/O model: https://learn.microsoft.com/en-us/windows-hardware/drivers/kernel/overview-of-the-windows-i-o-model
- Windows kernel managers: https://learn.microsoft.com/en-us/windows-hardware/drivers/kernel/