# Production Runtime Follow-up — 2026-10-22

## Exact-head scan

- Repository: `amerhwitat/ChimeraIIOS`
- Reviewed branch: `fix/stage-production-init-elf-modules-20261020`
- Reviewed head: `b3e243babb3c7580f65b61c9699ef9f99d62bab3`
- Tracking PR: [#187](https://github.com/amerhwitat/ChimeraIIOS/pull/187), still draft.
- Full ISO workflow: [run 39806135277](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39806135277); no job result was available from the workflow-job endpoint during this scan.
- Kernel workflow run 39806135205 had its x86_64 job queued at the latest poll.
- Current PR metadata reports mergeable=true. This is not a CI or runtime pass.

## Source-backed findings

1. `kernel/userspace/native_init.c` is a fail-closed diagnostic bootstrap. It attempts a user-originated interrupt acknowledgement, requests a kernel-owned PID, prints diagnostics, states that filesystem/process/device/graphics services are unavailable, then exits 78. It is not a production Live/Installer/Recovery runtime.
2. `kernel/core/syscall.cpp` has a limited native dispatch surface; file I/O, mapping, wait/reap and other declared calls do not yet form a complete process-owned userspace ABI. Do not replace unavailable operations with fake success.
3. `kernel/core/initramfs_ingest.cpp` performs bounded raw/gzip ingestion and validates the decompressed newc archive. Validation is not extraction or mounting: this code copies/decompresses to a workspace and calls `chimera_cpio_validate_newc`; it does not create VFS nodes.
4. The CPIO validator is not itself a safe extraction layer. Extraction must separately enforce path/type/duplicate/prefix-conflict/symlink policy and resource limits before exposing files to a process.
5. Historical full-ISO evidence recorded in the runtime gap audit showed the six target/firmware cases failing the production handoff. That historical result must not be represented as the current exact-head result.

## Required implementation sequence

1. Implement a bounded CPIO iterator/extractor with explicit accepted file types, path canonicalization, duplicate and file/directory-prefix conflict rejection, symlink policy (prefer reject until a safe resolver exists), byte/entry limits, rollback on any error, and adversarial tests.
2. Mount extracted nodes into a kernel-owned RAMFS/VFS namespace; implement lookup/open/read/close and process-owned descriptors with validated user buffers.
3. Complete process-owned memory mapping, user entry/return, task/PID ownership, wait/reap and exit teardown; add fault and cleanup tests.
4. Replace diagnostic native init with separate target-specific production init/service programs and explicit health handshakes.
5. Verify Live→Aurora, installer transaction plus cold reboot/read-back, and recovery repair postcondition.
6. Implement firmware-table AP discovery/startup and prove concurrent execution with per-CPU evidence.
7. Run the unchanged production verifier for Live/Installer/Recovery × BIOS/UEFI on the final ISO; preserve hashes and raw traces.

## Gate ledger

| Gate | Status |
|---|---|
| Bounded gzip/raw ingestion + CPIO validation | In review; exact-head CI pending |
| Safe extraction + mounted process-visible VFS | Not established |
| Complete process-owned syscall/FD lifecycle | Incomplete |
| Production Live/Installer/Recovery init and services | Not established |
| Aurora session health | Not passing / unverified |
| Installer persistence and installed cold boot | Not established |
| Recovery repair postcondition | Not established |
| AP startup and genuine concurrent SMP | Not established |
| Six production BIOS/UEFI cases | No new pass evidence |

## Release decision

Keep PR #187 draft and production publication blocked. Do not treat compilation, ISO composition, kernel-ready smoke, candidate ring-3 probes, a generic readiness line, or mergeability as production acceptance.
