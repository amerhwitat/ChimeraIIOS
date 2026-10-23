# Linux-to-Koronos bootability gap analysis

Date: 2026-10-23

## Purpose and boundary

Linux is a reference for interfaces and failure-handling patterns, not a binary/code drop-in for Koronos. Linux's x86-64 boot path, MMU setup, interrupt entry, scheduler, ELF loader, VFS, block layer, driver model, init execution, and service supervision depend on each other. Importing isolated Linux files without their configuration, architecture glue, memory-management invariants, locking, and licensing review would not make Koronos bootable and could create false confidence.

This document records the current source-level blockers and the implementation order. It does not claim runtime acceptance.

## Linux subsystem mapping

| Linux reference contract | Koronos equivalent / required work | Acceptance evidence |
|---|---|---|
| Architecture boot protocol, early console, IDT/GDT/TSS, APIC/PIT | Jasper/GRUB handoff, Koronos entry, descriptor tables, IRQ routing, per-CPU initialization | BIOS and UEFI boot logs; exceptions/IRQ diagnostics; no unexplained reset |
| start_kernel() and initcalls | explicit staged kernel initialization with dependency/failure propagation | ordered stage trace; fatal dependencies stop boot |
| mm/, page tables, allocator | frame allocator, process-owned CR3, ELF PT_LOAD mapping, stack and permissions | page-fault tests; W^X; address-space teardown; user pointer validation |
| kernel/entry/ and syscall tables | user_entry.asm, INT 0x80/SYSCALL dispatch, syscall ABI | genuine ring-3 origin, saved-CS/CR3/PID checks, syscall result observed by userspace |
| fork(), execve(), wait() and exit/reap | missing production spawn/exec/wait/reap lifecycle | child launch, exit status collection, PID reuse safety, descriptor/address-space cleanup |
| fs/ VFS and initramfs root | CPIO validation + transactional extraction + VFS root mount | ring-3 OPEN/READ/CLOSE on a known embedded file; malformed archive rollback |
| shmem/tmpfs-like writable volatile storage | bounded tmpfs mounted at /tmp | ring-3 CREATE/TRUNCATE/WRITE/SEEK/READ/CLOSE with exact byte comparison |
| block layer, partition/filesystem drivers, mount | installer storage discovery, writable target filesystem and explicit mount policy | disposable-disk install, sync, cold reboot, byte-for-byte readback |
| kernel threads/workqueues and userspace service supervision | actual child process supervision; current dependency/state bookkeeping is not a supervisor | services launched as processes, health checks, restart/failure policy, clean shutdown |
| DRM/fbdev/console and userspace compositor | framebuffer selection + Aurora compositor/session | selected mode evidence, compositor process health, display/session handoff |
| SMP boot and scheduler | AP startup, per-CPU state, IPIs, run queues and synchronization | AP online records plus overlapping work proven on two distinct CPUs |
| recovery tools and filesystem repair | recovery runtime + bounded repair operations | repair action followed by a verified filesystem/boot postcondition |

## Confirmed blockers

1. kernel/userspace/native_init.c is intentionally a diagnostic bootstrap: it tests syscall/VFS behavior and exits 78 with NATIVE INIT BLOCKED. It does not launch or supervise operational services.
2. kernel/core/target_launch.cpp stages and mounts Live/Recovery RAMFS and writable /tmp, but explicitly refuses Installer launch until a storage-backed root namespace exists. An installation image is not proof of a mounted writable disk filesystem.
3. kernel/core/syscall.cpp dispatches PID/time/yield and basic file/console operations for the active process, but there is no complete process spawn/exec/wait/reap contract wired into this path. A service dependency graph alone cannot launch aurora-session, install-executor, or recovery-runtime.
4. Existing CI has had successful compile/ISO-composition/QEMU-kernel-marker stages while the production userspace verifier failed to observe the required ring-3 syscall acknowledgement and matching PID readiness. Those are different acceptance layers.
5. The production closeout evidence JSON must be built from raw ISO hashes and captured traces. Unit tests for the checker, candidate payload probes, booleans in JSON, or hand-written logs are not production evidence.

## Check / Plan / Do / Act loop

### Check
- Inspect the exact commit and source API before importing or adapting code.
- Run the canonical build script, compiler warnings-as-errors host tests, CTest, ISO composition, and unchanged handoff/DAPS gates.
- Preserve raw build logs and QEMU serial/debugcon output for each run.

### Plan
1. First make ring-3 entry/syscall/return/exit reliable and diagnosable for all six target/firmware combinations.
2. Finish transactional archive extraction and process-visible root VFS; test both valid and adversarial archives.
3. Implement process lifecycle primitives (spawn/exec, wait/reap, exit status, descriptor/address-space cleanup) before operational service startup.
4. Add service supervision and real health probes; never let a module being present imply a service is healthy.
5. Implement installer block-device discovery, writable filesystem mount, transaction/rollback, sync, and cold-reboot readback.
6. Verify display/Aurora handoff, recovery repair postconditions, and AP-backed concurrent SMP independently.
7. Have the evidence collector record actual artifact hashes, per-case traces, and parsed observations. Missing observations must produce FAIL / NOT RUN, never PASS.

### Do
- Adapt concepts and small, self-contained algorithms only after API, architecture, and license review. Do not copy Linux internals into Koronos as a substitute for implementing their contracts.
- Add regression tests before changing fail-closed checks.
- Use the repository's canonical builder; do not claim a build if the toolchain or runtime was not executed.

### Act
- Repeat the loop for each root cause until a new run demonstrates the fix.
- Keep release publication blocked until all six production ISO cases and the independent Aurora, persistence, recovery, and SMP gates pass.
- Report each gate as PASS, FAIL, or NOT RUN with links to raw evidence and exact commit SHA.

## Production matrix

| Gate | Required proof | Current status |
|---|---|---|
| Live × BIOS / UEFI | ring-3 syscall + same nonzero PID readiness + rootfs I/O + tmpfs mutation + Aurora health | NOT ESTABLISHED |
| Installer × BIOS / UEFI | ring-3 syscall + same nonzero PID readiness + storage-backed install + cold-reboot readback | NOT ESTABLISHED |
| Recovery × BIOS / UEFI | ring-3 syscall + same nonzero PID readiness + rootfs I/O + tmpfs mutation + repair postcondition | NOT ESTABLISHED |
| Genuine SMP | AP online and overlapping execution on distinct CPUs | NOT ESTABLISHED |
| Evidence collector | actual production ISO SHA-256 + raw per-case traces + validated observations | NOT ESTABLISHED |

A source change is not considered fixed until the corresponding regression test and runtime evidence pass.
