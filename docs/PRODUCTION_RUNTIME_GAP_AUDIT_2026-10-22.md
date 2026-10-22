# Production Runtime Gap Audit — 2026-10-22

## Scope and evidence boundary

Reviewed the repository's native syscall ABI/dispatcher, ELF loader, scheduler and service bootstrap, native init, target-launch contract, current GitHub Actions run listings, and the production-handoff engineering notes in the project Library. This is a source audit, not a claim that every file in this large repository has been exhaustively compiled or executed.

## Confirmed implementation gaps

1. **Native init is intentionally a probe, not a target runtime.** `kernel/userspace/native_init.c` acknowledges CPL3 entry, reads the kernel-owned PID, prints diagnostics, explicitly reports that filesystem/process/device/graphics services are unavailable, and exits with status 78. It does not mount a root filesystem, launch the target's `/init`, supervise services, start Aurora, install an OS, or provide a recovery shell.
2. **Syscall coverage is incomplete.** `kernel/core/syscall.cpp` provides a narrow compatibility dispatcher. The declared READ, MMAP, MUNMAP, IOCTL, NANOSLEEP, WAIT, and ARCH_PRCTL semantics are not a complete usable userspace ABI in this dispatcher. The compatibility path rejects GETPID and EXIT when it has no process context; do not weaken these guards by returning a fabricated PID or pretending EXIT has reaped a process.
3. **Scheduler is not SMP.** `kernel/core/scheduler.cpp` explicitly returns zero from `chimera_sched_run_parallel()` because no AP workers enter the scheduler on independent CPUs. Callback sequencing is not evidence of concurrent AP execution.
4. **Service bootstrap is declaration-only.** The service bootstrap declares core services; it does not start their callbacks or health checks. Storage is not ready merely because a storage service ID exists.
5. **ELF loading is not process lifecycle.** The PT_LOAD/BSS/stack/W^X loader has unit coverage, but that does not implement a full VFS, exec/read/write lifecycle, wait/reap, process supervision, or target service manager.
6. **Production destination gates remain open.** Aurora session usability, installer writes plus reboot persistence, operational recovery, cold-boot storage persistence, and six independent production target/firmware cases remain unproven.

## Required engineering sequence

1. Implement bounded newc CPIO parsing and safe extraction, with explicit gzip/DEFLATE support or a fail-closed unsupported-compression error; reject path traversal, absolute paths, malformed headers, overflow, duplicate/invalid entries, and missing trailer.
2. Implement a kernel-owned VFS/RAMFS mount and path/file descriptor operations, then wire user-copy validation and READ/WRITE/MAP/UNMAP semantics to active process address spaces.
3. Implement process state, parent/child ownership, wait/reap, exit teardown, context switching and a PID-1 supervisor. Never treat a successful syscall round-trip as service readiness.
4. Add target service executables and independent health checks: Aurora compositor/session for Live; a destructive-operation-confirmed installer transaction on disposable storage; diagnostic shell and repair verification for Recovery.
5. Add block-device discovery/driver binding, persistent filesystem mount, flush/barrier semantics, and write → cold reboot → read-back acceptance.
6. Bring up APs from firmware tables, publish per-CPU state, enter scheduler workers concurrently, and prove overlapping execution with per-CPU evidence.
7. Run Live/Installer/Recovery × BIOS/UEFI on the production ISO. Preserve ISO and payload SHA-256, firmware command line, raw boot logs, target-owned service logs, exit codes, and explicit PASS/FAIL/NOT RUN.

## Release policy

Keep the production gate fail-closed. Do not substitute a generic init marker, a kernel log, an isolated probe ISO, static routing tests, or a sequential scheduler test for destination evidence. No production release is justified until all required evidence is captured.

## External architecture references

- Linux kernel initramfs/rootfs format and extraction lifecycle: https://www.kernel.org/doc/html/v6.5/filesystems/ramfs-rootfs-initramfs.html
- Limine boot protocol contract: https://github.com/limine-bootloader/limine-protocol/blob/trunk/PROTOCOL.md

These references guide design; no third-party implementation was copied into the kernel without a license, integration, and test review.


## Follow-up evidence — 2026-10-22

The corresponding OctavianOS recovery/UEFI production acceptance job (run 39774382031, job 119809533041) completed with FAILURE after building Koronos, high-address userspace probes, classifying the recovery module, building a target-specific ISO, and attempting the userspace readiness gate. The trace shows generic USERSPACE READY: recovery init pid=1, followed by userspace exit; the launcher reports that init exited before its target-specific handshake, then says recovery handoff is withheld because no native recovery init ELF/runtime is wired to the payload. Runnable task count is zero. This is not a recovery-runtime pass.

The log also contains PASS: ordered kernel/user-syscall/userspace-ready trace target=recovery pid=1; this is only a trace-order/probe assertion and must not override the later job failure or be interpreted as service readiness. Generic probe evidence and target service readiness are distinct gates.

## Implementation/acceptance ledger

- [ ] Bounded newc parser: validate magic, fixed-width hexadecimal fields, namesize/filesize, NUL termination, 4-byte alignment, trailer, and offset arithmetic before reading.
- [ ] Compression: support gzip/DEFLATE through a bounded decoder with compressed and expanded-size limits; reject unsupported formats explicitly.
- [ ] Extraction: reject absolute paths, '..', invalid components, duplicate/conflicting entries, unsupported file types, and symlink escape; enforce entry/count/total-byte limits.
- [ ] VFS/FD integration: mount extracted initramfs into a real namespace; connect per-process descriptor tables and validated user-buffer copies to real file operations; preserve permissions and fail closed for unsupported operations.
- [ ] Lifecycle: real exec/exit/wait/reap and address-space/descriptor cleanup; PID and readiness tied to the same live process and target-owned service.
- [ ] Targets: Live starts and health-checks Aurora; Installer executes a bounded transaction on disposable storage and verifies reboot persistence; Recovery provides a usable shell and commands.
- [ ] Storage/SMP: cold-reboot persistence evidence and AP startup plus concurrent execution on distinct CPUs.
- [ ] Matrix: six independent Live/Installer/Recovery × BIOS/UEFI results with ISO/payload hashes, full boot logs, syscall/PID evidence, service health evidence, and explicit PASS/FAIL/NOT RUN.

This ledger is not an implementation claim. Keep release blocked until each checkbox has executable evidence; a generic USERSPACE READY marker is not target-service proof.


## Source implementation update — 2026-10-22

A first executable archive-validation layer has now been added to the Koronos source tree and build script on this branch:

- `kernel/include/chimera/initramfs_cpio.h` defines a bounded validation API and explicit status codes.
- `kernel/core/initramfs_cpio.cpp` validates raw `070701`/`070702` newc headers, hex fields, bounds, alignment, NUL-terminated names, path traversal/absolute-path rejection, supported entry types, CRC checks for `070702`, entry/expanded-payload limits, and the `TRAILER!!!` terminator. It reports gzip as unsupported compression rather than accepting the envelope as a valid archive.
- `kernel/tests/initramfs_cpio_test.cpp` adds host regression cases for a valid archive, top-level `init`, truncation, path traversal, gzip rejection and size limits; `kernel/build-koronos.sh` compiles/runs this test and links the validator into Koronos.
- `kernel/core/target_launch.cpp` now validates raw Live/Recovery CPIO before launch and rejects gzip until a bounded decompressor is wired. The production readiness check now requires a target-owned service marker (`aurora-session`, `install-executor`, or `recovery-runtime`) rather than the generic native-init probe marker.

This is a real partial implementation, not a complete initramfs runtime. It does not yet extract files, mount a VFS, create process-owned file descriptors, implement exec/wait/reap, or start target services. Duplicate path names are now rejected by a bounded prior-entry scan, with a regression case added in `kernel/tests/initramfs_cpio_test.cpp`; directory/file prefix conflicts and full extraction semantics still require a VFS-aware extraction layer. Gzip/DEFLATE support remains absent, so compressed production initramfs deliberately fails closed. Host regression and kernel CI workflows triggered by these commits were queued at the last poll; no passing build/test claim is made here.
