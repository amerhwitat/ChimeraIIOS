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

## Follow-up scan — 2026-10-22, after production trace inspection

The actual three-target QEMU trace artifact confirmed that Live and Recovery failed before ring-3 because their gzip-compressed CPIO archives begin with the conventional root directory entry `., which `safe_path()` rejected. Installer reaches the real user-originated INT 0x80 acknowledgement and PID output, then correctly exits 78 because required native filesystem/process/device/graphics services are not available.

PR #187 now accepts only `. as a directory entry and adds raw/gzip ingestion and CPIO regression fixtures with that root entry (`631c2ed`, `a2bc99a`, `4d35e3e`). The full ISO build on the updated head is still pending; do not infer production acceptance from the unit fixtures. Rootfs extraction/mounting, complete process/syscall lifecycle, target services, Aurora health, installer persistence, recovery postcondition, and AP-backed SMP remain open gates.


## Exact-head recheck — 2026-10-22 17:53 UTC

The latest reviewed branch head is `a8b2314527336614825a081375cf93292f353d89` (the earlier head recorded above is historical).

Observed current-head checks:
- [Koronos Kernel Build #39824340412](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39824340412): **success**.
- [ELF process-loader unit tests #39824340673](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39824340673): **success**.
- [ISA/native command runtime #39824340352](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39824340352): **success**.
- [Hypervisor boot compatibility #39824340043](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39824340043): **success**.
- [VMware/QEMU boot matrix #39824340396](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39824340396): **in progress**.
- [Structured ISO #39824340019](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39824340019): **in progress**.
- [Full ISO #39824340040](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39824340040): **pending**.
- Earlier full ISO #39820468894 is still reported **in progress** by GitHub; no completed production handoff result was available in this poll.

A source re-read of `kernel/core/target_launch.cpp` confirms the remaining lifecycle blocker precisely: the gzip CPIO workspace is a local `TemporaryFrames` object and is freed at scope exit after validation; there is no extraction/mount operation before `chimera_arch_enter_user`. `kernel/userspace/native_init.c` explicitly exits 78 after reporting missing services. Therefore a passing kernel build and loader unit tests validate only those components; they do not validate a production rootfs or readiness.

No readiness marker, verifier relaxation, or release was added. Keep the production release gate blocked until a real process-visible filesystem and target services are implemented and all six production traces pass.


## Check/Plan/Do closeout loop — 2026-10-23

### Check: source-backed failures
- Production Live/Recovery initramfs is bounded-decoded and CPIO-validated, then extracted into an unpublished RAMFS staging tree. The launch path explicitly returns before ring-3 entry when a production payload exists because the staged rootfs is not mounted/published into a process-visible VFS. This is the direct reason those production cases cannot produce a real user-originated syscall/readiness handshake on this path.
- `kernel/userspace/native_init.c` is diagnostic-only by design. It performs an INT 0x80 acknowledgement attempt, requests kernel-owned PID, writes diagnostics, reports unavailable services, and exits 78. Do not relabel this as production init.
- Installer payload is a disk/image container and does not share the Live/Recovery CPIO extraction path; it needs a real installer execution and persistence test.
- Genuine AP startup and per-CPU scheduler workers are absent. CPU discovery is not CPU-online evidence; a loop over run_once() is serial, not SMP.
- No supported process-visible VFS bridge was found on the reviewed production branch; the expected standalone VFS source path returned 404. Do not invent an API or connect the 64-node/4-KiB legacy RAMFS as if it were production-capable.

### Plan: close blockers in dependency order
1. Implement a capacity-appropriate transactional extractor with canonical paths, duplicate/prefix conflict rejection, strict type/symlink policy, total-byte/entry limits, and rollback.
2. Implement atomic VFS root publication plus process-owned namespace/descriptors and validated user-buffer file syscalls.
3. Implement process exit/wait/reap and address-space teardown as one lifecycle contract.
4. Build target-specific production init/service programs; only emit readiness after required service health checks, tied to the same nonzero kernel-owned PID that issued a CPL3 syscall.
5. Implement real installer write/verify/cold-reboot/read-back and recovery repair/postcondition tests.
6. Implement AP discovery/startup, per-CPU state/worker startup and overlapping execution evidence before enabling multi-CPU scheduling.
7. Run unchanged production acceptance for Live/Installer/Recovery × BIOS/UEFI on the final ISO, archive raw traces and artifact hashes.

### Do: committed scheduler safety fix
- Commit `bf7683a22fef0ac27ae6501e53b759b61f21574c` initializes the scheduler with one online CPU until AP startup exists. This avoids assigning runnable work to CPUs that CPUID reports but the kernel has not started.

### Validation: observed, not inferred
- Historical exact-head evidence includes successful kernel build/loader tests but failed actual production target handoff; the full production verifier reported missing CPL3 acknowledgement and/or matching nonzero PID readiness. Those are failures, not a production pass.
- No workflow run was returned for the scheduler fix commit at the last lookup. Treat that as unreported, not passing.
- Production rootfs mount, production service health, all six BIOS/UEFI cases, Aurora, installer persistence, recovery repair, and genuine SMP remain unverified.

### Release decision
Keep PR #187 draft. Do not publish a production release until all seven dependency-order gates above pass. Never weaken the verifier, synthesize readiness, or count queued/cancelled/unreported checks as passing.


## Follow-up implementation — RAMFS root publication and read-only process file syscalls (2026-10-23)

Implemented on this branch:
- kernel/core/target_launch.cpp: after complete bounded CPIO extraction succeeds, atomically publish the immutable RAMFS root pointer for the selected Live/Recovery target. Installer remains fail-closed because its payload is a disk/image container and is not mounted by this path.
- Added process-bound descriptor slots tied to the active kernel-owned PID. open accepts read-only flags only; read validates the destination range against the active process CR3 and caps one operation at 4096 bytes; close checks descriptor ownership. Descriptors are reclaimed when init exits.
- kernel/include/chimera/syscall.h and kernel/core/syscall.cpp: add native OPEN/CLOSE IDs and route OPEN/READ/CLOSE into the rootfs bridge. Existing WRITE remains console-only; RAMFS file mutation is not implemented.
- tools/tests/test_native_init_launch_gate.py: extend the source-contract gate to require atomic publication, active-address-space validation, read-only open, and all three syscall routes.
- kernel/build-koronos.sh: require the new bridge symbols at link validation.
- Corrected the service readiness comment so the existing gate phrase “Registration is not a health check” remains explicit.

Commits: d261e1c03fe4f73258321d5dcadfc2d37d3aa713, 0fbbba9ae3df330394235b779df88e6607999f6e, ad575d86e8fb65f7aae992299afe2dbedb61f320, afd14a33d227570555715573988cb422594591f3, c5628efb2a6f4f95ceeca71d54c5e93cf19d5147, 494b4cd6bb4b8d5e7fb1be2e18a2cb9b538ab3f8.

Verification status: no workflow runs were reported for the latest source/link-gate commits at the latest connector poll; the tests/build have not been run locally in this session. Treat this as implemented but unverified. This is a narrow read-only RAMFS bridge, not a general mutable VFS or complete process file API. Service manager/supervision, Aurora session startup, installer write/verify/cold reboot, recovery repair postcondition, AP startup/concurrent SMP, and the six-case full production acceptance matrix remain open. Keep the PR draft and release blocked.
