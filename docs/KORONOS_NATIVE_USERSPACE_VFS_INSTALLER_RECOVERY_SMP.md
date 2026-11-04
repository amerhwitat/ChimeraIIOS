# Koronos native userspace, VFS, Installer, Recovery and SMP milestone

Status: engineering contract / implementation plan. This document is not evidence that the listed capabilities are implemented.

## 1. Scope and invariants

The target is a native Koronos userspace path shared by Live, Installer and Recovery. All three must use the same kernel-owned process and VFS contracts while retaining separate target policies and rootfs payloads. The implementation must fail closed: no readiness marker is synthesized by the kernel, no test ELF is promoted to production init, and no skipped case is counted as a pass.

Readiness is emitted by the actual target init process only after the same process has completed: CPL3 entry; a user-origin syscall with validated saved CS/RIP and active address-space identity; GETPID returning its kernel-owned nonzero PID; successful /etc/os-release open/read/close; and a write/read verification under /tmp. The PID in NATIVE INIT PID and USERSPACE READY must match.

## 2. Syscall and process architecture

Keep one canonical native syscall ABI. INT 0x80 is a DPL3 software interrupt and must validate the CPU-saved privilege frame; SYSCALL is a separate fast-entry mechanism and must validate the active process context because SYSCALL does not save caller CS. Both entry paths must converge on the same process-bound dispatcher after entry-specific validation. An acknowledgement proves origin only; it is not proof that a requested operation succeeded.

Introduce a kernel-owned process record with at least: PID, parent PID, lifecycle state, address-space root, guarded kernel stack, saved trap frame, user stack, credentials/capabilities, fd table, exit status, wait/reap linkage, CPU ownership and accounting. Define explicit transitions NEW -> LOADED -> RUNNABLE -> RUNNING -> BLOCKED or EXITED -> REAPED. Reject duplicate ownership, invalid state transitions and user pointers outside mapped user pages.

Process creation must be transactional: allocate address space and guarded stack, validate ELF headers/segments and entry point, map pages with W^X permissions, initialize the initial trap frame and per-process kernel stack/TSS.RSP0 handoff, then publish the PID as runnable. On any failure, unwind all pages and metadata. Exit must detach the task from scheduling, preserve status for wait, close descriptors, release address-space resources only when no CPU can still reference them, and allow the parent to reap exactly once.

## 3. VFS and first filesystem

Implement a small VFS layer before adding persistent filesystems: mount namespace/root, mount/superblock, inode, dentry, file object, file operations and per-process descriptor table. Start with a bounded in-memory tmpfs supporting directories, regular files, create, lookup, read, write, seek, truncate and close. Define ownership and reference-count rules before adding unmount.

Required syscall semantics: OPEN(path, flags, mode); READ(fd, user_buffer, length); WRITE(fd, user_buffer, length); SEEK(fd, offset, whence); CLOSE(fd). Validate and copy user paths/buffers through the active address-space page tables, check overflow and lengths, never dereference raw user addresses in kernel context, and return stable negative errno values. Add /dev/console as a separate character device rather than treating console output as the filesystem implementation.

Tests must cover create/write/read/seek/close/reopen, directory traversal, EOF, short reads/writes, invalid descriptors, invalid and cross-page user pointers, permission errors, allocation exhaustion and concurrent access. The boot acceptance test must read /etc/os-release and write/read /tmp from CPL3.

## 4. Linux early-userspace workflow to adapt

Use the Linux initramfs architecture as a workflow reference, not as a claim of Linux ABI compatibility: the bootloader loads the kernel and an initramfs; the kernel extracts a CPIO archive into a temporary root; the kernel starts the init program as PID 1; early userspace discovers buses and storage, loads or activates required drivers, assembles storage, mounts the real root and switches root before execing the next init. Keep the early root minimal and self-sufficient.

Live uses the early root as its operational root and starts the declared session stack only after VFS, device and service checks pass. Installer uses a separate initramfs/rootfs and service plan; it must not silently reuse Live readiness as installer readiness. Recovery uses a minimal independent root with read-only discovery and mount as its default.

## 5. Installer transaction

Installer phases: discover devices; identify stable device identity and capacity; display the selected whole disk and destructive effects; require explicit confirmation; validate firmware mode and partition plan; create GPT/ESP and required partitions; format; mount target root; install the immutable verified system payload; generate fstab-equivalent mount metadata; install and verify BIOS and/or UEFI bootloader according to the selected mode; sync and unmount; reboot into the installed system. Every write is journaled with device identity, byte ranges and result. Abort safely on device identity change or any failed phase.

Acceptance requires a disposable virtual disk, recorded before/after partition tables, filesystem checks, installed file hashes, bootloader verification, shutdown, a separate cold boot from the installed disk, and a persistence check. A dry-run plan is useful preflight but is not an installation.

## 6. Recovery transaction

Recovery phases: boot independent recovery root; enumerate installed systems; mount candidate volumes read-only; collect logs and metadata; assess selected repair; request explicit authorization for writes; create backups or snapshots where supported; execute one bounded repair transaction; sync; remount/check; verify a concrete postcondition; report exactly what changed. A diagnostics-only boot is not repair acceptance.

Test with intentionally damaged boot configuration, filesystem metadata in a disposable image, and recoverable package/system-file corruption. Verify both successful repair and refusal when the target is ambiguous or the repair preconditions fail.

## 7. Genuine SMP

Discover CPU topology from firmware tables; start APs using a platform-correct SIPI trampoline; initialize per-CPU GDT/TSS/GS, interrupt controller state and idle context; publish AP-online acknowledgement; provide IPI-based reschedule/wakeup and TLB shootdown; implement scheduler-owned saved contexts and synchronization. Do not use serial callback stepping as SMP evidence.

Acceptance requires at least two independently executing vCPUs, AP startup acknowledgements, per-CPU identity records, concurrent work intervals that overlap in monotonic time, IPI wake/reschedule, cross-CPU TLB invalidation, lock/atomic stress and repeatable raw logs. Keep parallel scheduling disabled until these tests pass.

## 8. Same-ISO release matrix

Build one immutable ISO once and record its SHA-256 and embedded init ELF hashes. Do not remaster or modify it between tests. Run Live/Installer/Recovery under BIOS and UEFI (six cases), recording firmware mode, emulator version/configuration, ISO SHA, target init ELF SHA, serial trace, actual init PID, CPL3 syscall proof, VFS tests, target-specific health and final exit state. Installer additionally records the cold-reboot/persistence trace; Recovery records repair/postcondition trace; SMP records AP/concurrency trace.

The verifier must reject missing traces, duplicate or mismatched ISO hashes, zero or mismatched PIDs, kernel-originated rather than user-originated syscall evidence, missing VFS operations, and any test whose target-specific postcondition is absent. The same immutable ISO SHA must appear in all six cases.

## 9. Current source boundary

The current branch contains a single-process CPL3 entry/return foundation, ELF segment/address-space loading, a callback scheduler and a limited syscall path. The DPL3 INT 0x80 handler currently records privilege-origin evidence rather than implementing VFS operations. The generic compatibility syscall dispatcher has no active process context for GETPID/EXIT. The scheduler parallel API remains fail-closed. Installer and Recovery target init programs are currently dry-run/diagnostic payloads. These boundaries must be updated only when source and raw test evidence change.

## 10. References

- Linux kernel: Ramfs, rootfs and initramfs — https://docs.kernel.org/filesystems/ramfs-rootfs-initramfs.html
- Linux kernel: Using the initial RAM disk (initrd), including root handoff and installation workflow — https://cdn.kernel.org/doc/html/latest/admin-guide/initrd.html
- Linux kernel x86 boot protocol — https://www.kernel.org/doc/html/latest/arch/x86/boot.html

These references describe Linux's implementation. Koronos must implement and test its own ABI, data structures, drivers and lifecycle.

## 11. Current implementation update (2026-11-04)

The kernel now contains a bounded in-memory root namespace with a read-only `/etc/os-release` entry and a separately enabled `/tmp` tmpfs area. The native user syscall path has been extended with OPEN (17), READ (8), WRITE (9), SEEK (19), and CLOSE (18). File descriptors are currently a bounded table scoped to the single active bootstrap init process; they are reset before target entry and closed on process exit. User path and buffer ranges are checked against the active address space before kernel access. The three target init payloads now require a CPL3 round-trip test: open/read/close `/etc/os-release`, create/write/seek/read/close `/tmp/koronos-acceptance`, compare the returned bytes, and only then emit their readiness line.

This is an initial native syscall/VFS integration, not a production general-purpose filesystem. The current root is an in-memory bootstrap filesystem, not a CPIO-newc initramfs extraction or persistent block-backed root; directory/inode/mount namespaces, independent per-process descriptor tables, descriptor inheritance, concurrency, permissions and robust error handling still require implementation and tests. A successful host VFS test is not CPL3 guest evidence; only the target QEMU traces can establish that.

The VFS host regression is included in `kernel/build-koronos.sh`. OctavianOS vendors the matching VFS source/header, syscall dispatch, target init payloads, host test and build hook. Current CI is required to compile and execute these changes before any implementation status is promoted.

No AP trampoline, MADT/LAPIC startup, per-CPU TSS/GS initialization, IPI rescheduling or measured concurrent execution has been added. `chimera_sched_run_parallel()` remains fail-closed. No graphical Aurora/Marine processes are launched by the native Live init. Installer remains a dry-run payload with no block-device write backend or cold reboot. Recovery remains diagnostic and performs no repair transaction. These are intentionally still blocked, not inferred from the desktop shell or host tools.
