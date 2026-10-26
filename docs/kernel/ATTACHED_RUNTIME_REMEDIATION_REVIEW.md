# Review of attached kernel/userspace/DAPS remediation proposal

Date: 2026-10-23  
Scope: review of the attached proposal against the current Koronos source on `audit/koronos-cross-os-syscall-roadmap-20261023`.

## Decision

The attached snippets are useful as a problem inventory, but they are **not safe to merge as production implementation**. Several use APIs and headers that do not match the repository, and multiple “health”/readiness paths would report success without performing the claimed operation. Do not replace `tools/production-closeout-daps.py` with the shorter proposed `scripts/daps_validator.py`: the existing verifier enforces substantially stronger production evidence.

## Findings by phase

### 1. Rootfs publication and descriptor binding

- The proposed `<kernel/vfs.h>`, `<kernel/process.h>`, `kernel_log`, `copy_from_user`, `vfs_node`, `vfs_lookup`, and `process_alloc_fd` API set is not the API used by the current tree. Current interfaces live under `kernel/include/chimera/`, with `chimera_vfs_mount`, `chimera_vfs_open/read/write/seek/close`, and a RAMFS-backed mount adapter in `kernel/core/target_launch.cpp`.
- Assigning a global pointer is not a VFS mount/publication transaction. The current target launcher already has staging/published-root state and should be repaired at the actual mount and launch boundary, not bypassed with an unrelated node type.
- The proposed `sys_open` copies a fixed 255 bytes without a demonstrated user-range validation contract or bounded NUL-termination check. It also does not bind an FD to the active process safely, check access flags, or protect root publication against concurrent readers.
- Generation-safe descriptor handles and process teardown must be implemented through the existing VFS/process contracts, not guessed APIs.

### 2. Service orchestration

- The example `check_vfs_health`, `check_storage_health`, and `check_graphics_health` all return `true` unconditionally. They are placeholders, not health probes, and must never authorize readiness.
- The proposed `SYS_EMIT_READY = 4` conflicts with the current native semantic ABI where `CHM_SYS_TIME_TICKS = 4`. Treating it as a readiness syscall would invoke the wrong operation, not emit a component handshake.
- A loop over a static array is not a dependency-aware supervisor: there is no process spawning, dependency ordering, restart/backoff, exit monitoring, timeout, or real health check. Critical failures must remain fail-closed.

### 3. Aurora session

- The framebuffer, input, and compositor initialization steps are comments, not implementation. A successful syscall would therefore not prove a display is active.
- Executing `hlt` from ring 3 is privileged and will fault; it is not a userspace event loop or blocking wait.
- The snippet's inline `int 0x80` register convention has not been tied to the kernel's saved-frame ABI, pointer validation, active PID/CR3 checks, or the exact readiness contract. It cannot safely emit production readiness.
- Do not add a new readiness syscall number until the ABI, handler, user-memory rules, and negative tests are specified and implemented.

### 4. DAPS verifier

The attached shorter verifier is weaker than the existing `tools/production-closeout-daps.py`. It only searches for a readiness substring and does not enforce the existing full requirements: target-matched nonzero user-originated syscall PID and readiness PID equality/order, process-visible rootfs file syscalls, tmpfs mutations, display mode evidence, Aurora handoff, installer cold-reboot persistence, recovery repair, and AP-backed overlapping execution on at least two CPUs. Replacing the current gate would silently downgrade release safety.

The existing verifier was retained. This change only makes an unreadable raw trace produce an explicit fail-closed validation error instead of an uncaught exception.

### 5. Release matrix claims

The attached table labels all six VFS/process and service-health cells “Implemented/Passed”, but the attached material does not provide raw, hash-bound QEMU logs or production artifacts proving those claims. Those statuses are not accepted as evidence. Release stays blocked until the existing DAPS verifier passes on actual evidence for all six target/firmware cases.

## Required implementation order

1. Reproduce and fix failures against the actual repository APIs; add regression tests before changing the production path.
2. Prove the initramfs-to-RAMFS/VFS root mount with a process-originated OPEN/READ/CLOSE sequence and validated user buffers.
3. Complete process-owned FD lifecycle and generation-safe handles; add stale-handle, bad-pointer, and process-exit tests.
4. Implement real service process supervision and health probes; readiness is emitted only after a real operation succeeds.
5. Complete installer storage discovery/write/sync/readback/cold-reboot verification and recovery repair/postcondition tests.
6. Implement framebuffer selection/fallback and Aurora handoff; readiness requires a working compositor/session, not just a marker.
7. Prove AP startup and overlapping work on distinct CPU IDs.
8. Run the production six-case BIOS/UEFI matrix, bind every trace to the exact production ISO SHA-256, and pass the unchanged DAPS gate.

## Check → Plan → Do → Act result

- **Check:** proposal reviewed against current interfaces and ABI.
- **Plan:** dependency order above; no parallel claims of completion.
- **Do:** hardened DAPS handling for an unreadable raw trace; retained fail-closed checks.
- **Act:** CI and production evidence still required. No runtime readiness, six-case acceptance, or release success is claimed by this review.
