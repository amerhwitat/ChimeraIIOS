# Transactional RAMFS and Process File-Descriptor Integration

Status: **design proposal / not production implementation**. This document records the requested dynamic RAMFS, transactional extraction, and process-owned FD work while preventing placeholder code from being mistaken for a working filesystem.

## Root cause this change must resolve

The current Koronos path validates raw CPIO or bounded-decompresses gzip CPIO into temporary frames. Validation does not publish a mounted filesystem or make archive paths visible to the launched init process. The production init bootstrap therefore has no complete rootfs/service path and intentionally fails closed. The current kernel build's explicit source list includes CPIO validation and ingestion but no RAMFS/VFS implementation; do not add unintegrated source files and call that fixed.

## Review of the supplied snippets

The submitted snippets are useful as a sketch, but must not be copied verbatim into production:

1. `tx_log_creation()` silently ignores journal-allocation failure. The node then becomes untracked and cannot be rolled back.
2. `ramfs_rollback_transaction()` frees nodes without unlinking them from their parent; parent child lists can retain dangling pointers. It also does not define rollback ordering for parent/child nodes.
3. The archive loop contains placeholder parsing and never validates actual CPIO fields, path collisions, parent types, trailer, bounds, or payload checksums.
4. `name[256]` plus truncating `strncpy` makes distinct long names collide. Reject overlong names; never silently truncate.
5. `new_size + 4096` can overflow. A claimed unlimited heap buffer is not acceptable for untrusted initramfs data.
6. The FD example assumes `proc->fd_table` and a VFS node layout that are not part of the current `chimera_process_image` admission-only API. It also does not define ownership, locking, close semantics, reference counts, or copy-to-user validation.
7. The snippets do not implement `open`, `read`, `close`, `execve`, path resolution, process teardown, or wait/reap.

## Required implementation contract

### RAMFS
- Use kernel-supported allocation/page APIs, with explicit maximum archive bytes, entry count, path length, total file bytes, and per-file size.
- Keep names untruncated and NUL-terminated; reject unsupported types (including symlinks/hardlinks until explicitly safe).
- Use a hierarchical directory tree with explicit ownership, reference counts or single-owner transaction semantics, and checked arithmetic for every allocation and offset.
- Reject duplicate normalized paths and file/directory prefix conflicts; allow the archive's canonical `.` root entry only as a directory.
- Keep an unpublished staging root until extraction and verification fully succeed.

### Atomic CPIO extraction
1. Preflight the entire newc/crc archive with bounded parsing before mutating the visible namespace.
2. Build staging nodes and payloads under a transaction journal. Every allocation must be journaled immediately; journal-allocation failure must itself fail the transaction.
3. On failure, unlink children safely and free every staged allocation in reverse dependency order. The live root must remain unchanged.
4. On success, publish the staging root atomically under the VFS/rootfs lock; do not expose partially populated paths.
5. Test malformed headers, arithmetic overflow, truncated names/data/padding, missing trailer, duplicate paths, path traversal, prefix conflicts, unsupported links/types, allocation-failure injection, entry/byte limits, and raw/gzip parity.

### Process-visible file descriptors
- Add FD state to the actual kernel process control block (not the ELF admission-plan record), with descriptors 0/1/2 initialized intentionally and a bounded per-process limit.
- Resolve absolute paths against the process root/cwd policy; validate user buffers and copy bounded data safely.
- Implement `open`, `read`, `close`, and then `execve` only after executable permissions, ELF validation, and address-space setup are integrated.
- Define descriptor duplication/inheritance, offset semantics, error ABI, node lifetime, exit cleanup, and synchronization.
- Never emit readiness from kernel-side parsing or tests. A readiness marker must originate from the launched CPL3 process and be tied to the same nonzero kernel-owned PID as its syscall acknowledgement.

## Integration sequence and acceptance gates

1. Define and review the VFS/node/allocation APIs against the actual freestanding kernel ABI.
2. Implement RAMFS + transaction journal and host-side deterministic unit tests, including allocation-failure injection.
3. Add the sources to the explicit kernel build list only after they compile under the project's freestanding flags.
4. Add rootfs publication to the production target-launch path, retaining fail-closed behavior on every error.
5. Integrate process-owned FDs and syscall routing.
6. Boot production-payload ISOs for Live, Installer, and Recovery under both BIOS and UEFI; run the unchanged production verifier.
7. Keep release blocked until all six cases prove user-originated CPL3 syscall acknowledgement and same-PID userspace readiness, followed by Live→Aurora, installer persistence, recovery postconditions, and genuine AP/concurrent-SMP evidence.

This document is a tracked engineering contract, not evidence that these gates have passed.


## 2026-10-22 implementation progress (candidate branch)

A bounded RAMFS staging API has now been added as `kernel/include/chimera/ramfs.h` and `kernel/core/ramfs.cpp`, with a host test at `kernel/tests/ramfs_test.cpp`. The source is included in the Koronos source list, and the host test is invoked by the kernel build script. OctavianOS mirrors these files under `vendor/chimera-ii-os/source/kernel/`.

Implemented in this candidate:
- allocator callbacks instead of an assumed `kernel_alloc` ABI;
- bounded CPIO parsing with a full existing CPIO validator preflight;
- dynamic tree nodes and file buffers with explicit archive/path/file/total/node limits;
- canonical component validation, duplicate and file/directory conflict rejection;
- fail-closed rejection of unsupported file types;
- an unpublished staging root returned only after complete extraction; all staged allocations are destroyed on failure;
- read-only lookup/read helpers and a host regression for extraction, reading, traversal rejection, and duplicate-archive rollback.

Still **not production integrated or verified**:
- The allocator callbacks are not yet bound to a production kernel allocator / frame-backed arena.
- The staging root is not yet atomically published through the existing VFS; `target_launch.cpp` still validates/decompresses the archive and then proceeds without exposing its files to init.
- Process-owned FD tables and `open/read/close/execve` syscalls are not implemented.
- The current VFS remains bounded and is not replaced by this staging API.
- New build/test workflows are queued; no test pass is claimed until their results are observed.
- Production six-case BIOS/UEFI readiness, Aurora handoff, installer persistence, recovery postconditions, and genuine SMP remain release gates.

The implementation deliberately does not emit or synthesize a userspace readiness marker. Do not merge or publish a production release until the above integration and acceptance evidence exists.
