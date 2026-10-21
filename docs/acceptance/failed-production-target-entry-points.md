# Failed production-target entry points

Status audited against the trace-producing Koronos source. This document is an implementation map, not a claim that userspace or SMP is working.

## Live userspace — blocked

- **Current entry point:** `kernel/core/koronos.cpp::task_live`.
- **Module discovery:** `chimera_multiboot_find(CHIMERA_MODULE_LIVE_INITRAMFS)`, populated by `kernel/core/multiboot_modules.cpp::chimera_multiboot_scan`.
- **ELF admission API:** `kernel/core/process.cpp::chimera_process_admit_elf`, declared in `kernel/include/chimera/process.h`.
- **Why it fails:** `task_live` logs “Runtime handoff queued” then blocks. The process API records an ELF load plan; it does not map PT_LOAD segments into a process address space, construct a ring-3 frame, enter the ELF entry point, or prove a syscall returned from user mode. Trace says runnable tasks are zero.
- **Required implementation seam:** replace the log-and-block branch in `task_live` with a selected-target launcher that obtains a verified init ELF from the live initramfs, validates it, maps segments with W^X and user permissions, builds a user stack, installs per-process page tables and kernel entry stack, and calls the architecture-specific ring-3 transition. Do not print readiness until a user-originated syscall is acknowledged for the same PID.

## Installer userspace — blocked

- **Current entry point:** `kernel/core/koronos.cpp::task_installer`.
- **Input modules:** installation image, manifest, contract, phases, and profiles, classified by `chimera_multiboot_scan`.
- **Why it fails:** the phase switch only logs metadata progress. Phase 3 explicitly says graphical installer userspace is not running; phase 4 blocks waiting for a loader that is not connected.
- **Required implementation seam:** keep metadata validation, but pass the verified installer init ELF and arguments to the same process-launch primitive used by Live. Require a real ring-3 entry and syscall evidence before reporting installer readiness. Installer storage writes must remain blocked until disk discovery, partitioning, filesystem mounting, and durable write/readback tests pass.

## Recovery userspace — blocked

- **Current entry point:** `kernel/core/koronos.cpp::task_recovery`.
- **Input module:** `CHIMERA_MODULE_RECOVERY_INITRAMFS`, classified by `chimera_multiboot_scan`.
- **Why it fails:** module acceptance is followed by “repair shell has not been entered”, then the task blocks. No shell ELF execution or repair command evidence is present.
- **Required implementation seam:** resolve a recovery init ELF and shell from the archive, launch them through the shared process-launch primitive, and test at least one read-only diagnosis plus an explicitly scoped repair/write with post-write verification. Never claim recovery readiness from module registration alone.

## Shared prerequisites before any target can pass

1. **ELF loader:** `chimera_process_admit_elf` is admission/validation only. Add physical-frame allocation, page-table mapping, BSS zeroing, page permissions, stack mapping, and architecture transition. Reject overlapping or non-user ranges and W+X segments.
2. **Authoritative process context:** bind syscall entry to the currently running process/PID and its address space; do not accept caller-supplied PID/UID/GID as authority.
3. **Safe user memory:** copy paths, strings, and buffers through a range-checked user-copy interface; never pass raw ring-3 pointers to VFS.
4. **Process-owned descriptors:** move the descriptor table into process state; close descriptors on exit; validate fd ownership and read/write permissions. Only then add canonical native OPEN/CLOSE/SEEK and VFS syscall dispatch, with explicit ABI tests.
5. **Initramfs filesystem:** parse bounded CPIO entries, reject malformed archives and path traversal, mount the archive read-only, and resolve executable paths from the selected target only.
6. **Exit/wait lifecycle:** connect EXIT/EXIT_GROUP to scheduler state transition, descriptor cleanup, and wait/reap; current compatibility dispatcher intentionally fails closed.
7. **SMP:** current `koronos_boot` calls `chimera_sched_init(1)`; AP startup, per-CPU stacks/interrupt state, and concurrent dispatch are absent. Do not infer SMP from serial scheduler stepping.

## Acceptance matrix and release rule

Run Live, Installer, and Recovery independently under BIOS and UEFI (six separate runs). Each case must record firmware, target payload identity/hash, PID, ring-3 entry, user-originated syscall acknowledgement, exit/wait behavior, filesystem read/write evidence where applicable, and the raw debug trace. Mark unrun cases NOT RUN, not PASS. Genuine SMP requires AP startup plus simultaneous execution evidence on distinct CPU IDs. Keep release publishing blocked until every required production case has independently passed.

## Trace-producing functions to update first

- `kernel/core/koronos.cpp::task_live`
- `kernel/core/koronos.cpp::task_installer`
- `kernel/core/koronos.cpp::task_recovery`
- `kernel/core/koronos.cpp::koronos_boot` (currently online scheduler CPU count is hard-coded to one)
- `kernel/core/process.cpp::chimera_process_admit_elf` (validation only; not an executor)
- `kernel/core/syscall.cpp::chimera_syscall_dispatch` (compatibility dispatcher without authoritative process context)
- `kernel/core/vfs_fd.cpp` and `kernel/core/vfs.cpp` (RAM-only primitives; not yet a secure process-backed syscall path)
- `kernel/core/cpio.cpp::chimera_cpio_find` (bounded lookup primitive; not a mounted filesystem)


## Appended engineering update — 2026-10-21

The earlier analysis above is the historical baseline; the following changes supersede the listed missing-bridge items, but do not claim target readiness.

### Implemented since that baseline

- Added the physical frame allocator and isolated address-space backend to the production Koronos build, including ELF segment mappings, user PTE permissions, BSS/stack setup, and the x86-64 GDT/TSS/SYSCALL entry path.
- Fixed a concrete bootstrap paging mismatch: the address-space clone requires all four PDPT entries for the 4-GiB identity map, while entry.asm had initialized only PDPT[0]. All four entries are now populated. EFER.NXE is enabled before executing NX-protected user mappings.
- Connected target-selected native-init ELF launch for Live, Installer, and Recovery. The full-ISO handoff harness now stages the actual native-init ELF in each target-specific ISO instead of omitting the user init module.
- Added a fail-closed native init that performs CPL3 INT 0x80 acknowledgement, obtains its process PID, and exercises RAM-VFS create/write/seek/read/stat/chmod/chown/truncate/close/rename/unlink/mkdir/rmdir syscalls. It exits with status 78 and never prints USERSPACE READY because persistent storage and production target services are still unavailable.
- Added VFS file and directory operations, typed stat results, serialized filesystem/descriptor access, PID-bound descriptor checks, user-range validation, and descriptor cleanup on exit/timeout. Installer and Recovery log messages were corrected so metadata inspection is not described as services having started.

### Still blocked

The RAM VFS is volatile and bounded. There is no persistent block-storage path or production FAT/ext2/ISO9660 implementation, no mounted/decompressed initramfs, no Live desktop startup, no durable installer disk transaction/reboot, no recovery repair shell, and no proven AP startup or genuine concurrent SMP. General multi-process credentials and wait/reap semantics also remain incomplete.

The production acceptance gate must remain strict. A passing kernel build, host VFS test, QEMU boot smoke, or candidate probe is not a production PASS. The six target/firmware cases must show the real init PID, CPL3 syscall acknowledgement, target-native readiness, and actual target operation. Current native init intentionally withholds readiness and exits 78; release publication remains blocked until those service implementations and full-ISO runs pass.
