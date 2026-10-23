# Production runtime acceptance status — ChimeraIIOS

Last updated: 2026-10-19

## Release decision

**BLOCKED. Do not publish a production ISO.** A kernel build, ELF validation, payload staging, or ring-3 smoke probe is not proof that production userspace starts.

## Latest cross-repository evidence

- OctavianOS [ring-3 smoke probes #39271188845](https://github.com/amerhwitat/OctavianOS/actions/runs/39271188845): all six Live/Installer/Recovery × BIOS/UEFI probe jobs passed. These are explicitly test-only probes.
- OctavianOS [native Koronos build #39271192234](https://github.com/amerhwitat/OctavianOS/actions/runs/39271192234): kernel and supporting payload build steps passed, but production-init ELF validation failed because the staged ISO was missing:
  - `boot/live/user-init-live.elf`
  - `boot/installer/user-init-installer.elf`
  - `boot/recovery/user-init-recovery.elf`
- The full-ISO routing/userspace checks and prerelease were skipped. Only the kernel ELF artifact uploaded; no production ISO was published.

## Source audit blockers

- The process interface still defines `CHIMERA_PROCESS_LOAD_PLAN_ONLY`; process admission is not a scheduler-backed execution lifecycle.
- The ELF loader prepares segment mappings and a stack, but does not activate a process-owned address space or enter CPL3.
- IDT entries are DPL0. A verified GDT/TSS/RSP0 and safe ring-3 interrupt/return path are not connected.
- The syscall dispatcher is a semantic dispatcher rather than a CPU syscall entry/return path; GETPID currently returns a constant, and EXIT/EXIT_GROUP do not perform process teardown.
- Architecture initialization detects logical CPU count but does not start application processors or prove concurrent per-CPU execution.

Do not create marker-only or probe-derived production init ELFs to bypass these blockers.

## Acceptance matrix

| Requirement | Status |
|---|---|
| ELF loader hardening and regression tests | Implemented; regression tests integrated |
| Six ring-3 smoke probes | PASS — test-only, not production acceptance |
| Production Live init ELF | MISSING |
| Production Installer init ELF | MISSING |
| Production Recovery init ELF | MISSING |
| Actual user-originated CPL3 syscall ACK with same kernel-owned nonzero PID | NOT VERIFIED |
| Live init → Aurora startup | NOT VERIFIED |
| Real installation → reboot → installed-system boot | NOT VERIFIED |
| Real Recovery operation | NOT VERIFIED |
| AP-backed concurrent SMP with per-CPU evidence | NOT VERIFIED |
| Six full-ISO BIOS/UEFI production cases | NOT VERIFIED |
| Production ISO release | BLOCKED |

## Required implementation and proof sequence

1. Implement process-owned address-space activation, validated mappings, GDT/TSS and per-process kernel stack, safe CPL3 entry/return, and fault/interrupt handling.
2. Implement a real syscall entry/return ABI with validated user arguments, kernel-owned PID identity, and working process exit/cleanup and scheduling lifecycle.
3. Build distinct, meaningful Live, Installer and Recovery init/service ELFs and stage each at its exact target path through the production ISO builder and Multiboot2 handoff.
4. Run the unchanged fail-closed production verifier against full BIOS and UEFI ISO boots for all three targets; capture per-case traces and matching user-originated acknowledgement/readiness PIDs.
5. Separately prove Live→Aurora, disposable-disk install→reboot→installed boot, a real Recovery action, and AP-started concurrent SMP.
6. Publish only after all mandatory gates pass and artifacts/traces are available for review.

A passing smoke matrix is useful regression evidence, but it does not change the production statuses above.

## Runtime implementation parity update — 2026-10-19

The native x86-64 ring-3 runtime foundation from OctavianOS's smoke-tested vendored Chimera source has now been synchronized into this ChimeraIIOS branch. This includes the frame allocator and process address-space backend, target ELF launch path, user-entry/TSS/SYSCALL assembly, interrupt/syscall integration, Multiboot user-init module classification, target launch integration in Koronos, and the build script wiring. The source-level parity is committed, but it is not yet considered validated in ChimeraIIOS until its own new six-case smoke workflow completes.

The new workflow is deliberately named **Koronos Ring-3 Smoke Probes (not production acceptance)**. It builds test-only payloads and does not establish Live-to-Aurora, installer completion/reboot, recovery operation, or AP-backed SMP.

**Production remains blocked:** no production service ELFs are created by the smoke-probe build. The three required boot/live/user-init-live.elf, boot/installer/user-init-installer.elf, and boot/recovery/user-init-recovery.elf payloads still need genuine target implementations and production ISO routing. Do not copy kernel/tests/user_init_smoke.c outputs into production paths. No release is authorized by this parity sync.

### CI integration corrections

The first new parity-workflow attempt exposed two integration issues: the copied Octavian workflow still used the vendored-source checkout path, and Chimera's x86-64 entry assembly did not export the bootstrap PML4 symbol required by the newly synchronized address-space backend. The workflow now uses the repository root, and entry.asm was synchronized to export koronos_bootstrap_pml4. Validation is pending in smoke matrix #39274513629, native build #39274513564, and loader tests #39274513527. Do not treat queued jobs as passing evidence.

### Native build result — 2026-10-19

The synchronized runtime foundation now passes the ChimeraIIOS native Koronos Kernel Build workflow #39274513564: ELF64 build, protected-process admission, ELF validation, and unresolved-symbol checks all passed. This is compile/link evidence only. The six-case smoke workflow #39274699829 has now completed successfully: all six test-only Live/Installer/Recovery × BIOS/UEFI probes passed, including the user-originated readiness handshake. This validates the smoke launch path, not production service behavior. Production init ELFs and target services remain absent, so full-ISO acceptance and release remain blocked.


## Cross-repository production-init root cause — 2026-10-19

The latest OctavianOS native build [#39275559014](https://github.com/amerhwitat/OctavianOS/actions/runs/39275559014) confirms the next blocker is beyond the already-passing ring-3 smoke foundation. The ISO builder invokes the production ELF validator but has no production init compile/stage rule before it; GRUB target entries also do not pass the kernel a `chimera-user-init-elf` module. The current syscall ABI exposes only PID, yield, ticks, console write, and exit operations; it does not yet expose the filesystem/process/device/graphics contract needed to consume the existing cpio initramfs and start Aurora or perform actual installer/recovery work.

The shell `/init` scripts in Live/Recovery cpio images are not equivalent to the native ELF modules expected by `koronos_launch_selected_userspace()`. Do not add a marker-only ELF or reuse `kernel/tests/user_init_smoke.c` as production payload. The required next implementation is a supported initramfs execution model or a real native userspace ABI/service layer, three target-specific init programs, production build/staging rules, and matching GRUB module routing. Full acceptance must then separately demonstrate Live→Aurora, disposable-disk install→reboot→installed boot, a real Recovery action, AP-backed SMP, and all six target × firmware boots.

As of this update: native kernel and six smoke probes PASS; production init ELF build/routing MISSING; full production acceptance NOT VERIFIED; ISO release BLOCKED.


## Native target init ELF build and routing update — 2026-10-19

Added the shared freestanding x86-64 target-init source and linker layout at `kernel/userspace/native_init.c` and `kernel/userspace/native_init.ld`, plus `tools/build-production-init-elfs.sh` to compile and stage the three target-specific files at the exact paths checked by the production ELF validator. `boot/iso/build-iso.sh` invokes this build after ISO layout preparation and before structural validation. Main GRUB and Jasper target menus now pass the appropriate `chimera-user-init-elf target=live|installer|recovery` module.

These are deliberately fail-closed bootstraps, not complete production userspace: they verify kernel-owned PID lookup and console syscall behavior, report that the native filesystem/process/device/graphics service layer is missing, and exit with status 78. They do not emit `USERSPACE READY` and cannot satisfy production acceptance. This work addresses ELF compilation, staging, and target routing, but does not implement the actual Live desktop, disk installer, or recovery service.

Latest verification pending CI. Release remains blocked until real target-specific service behavior, Live→Aurora, install/reboot, Recovery operations, AP-backed SMP, and all six full-ISO BIOS/UEFI cases are proven.


### Build validation note
A local freestanding compile/link check initially exposed 32-bit absolute relocations at the 4 GiB user-image base. The build flags now explicitly use `-mcmodel=large`; a repeated compile/link check produced all three ELF64 ET_EXEC files with one RX PT_LOAD segment at `0x100000000`. This is compile/link evidence only, not QEMU runtime or production acceptance. Repository CI for the branch is queued at the last status check.


## Exact-head remediation cycle — 2026-10-22

- Mirrored the production-rootfs fail-closed guard in `kernel/core/target_launch.cpp` (`af4ceb14938bd1a08ef9015b17db02a6ad8fff74`) because the launch path did not extract/publish the validated root payload before entering the separately staged init ELF.
- Mirrored precise CPIO-to-RAMFS error mapping in `kernel/core/ramfs.cpp` (`c16306b1fbd8920d2fc360824ac9fe60bc5a8653`) after OctavianOS explicit ELF smoke exposed a regression at RAMFS test line 62. The test failed because a CPIO type-validation error was reported as a generic header error.
- Source-level changes are present, but no workflow run has been returned for the current ChimeraIIOS PR head. Compile/test confirmation is pending.
- The guard is intentionally fail-closed, not a claim that rootfs publication, full userspace syscalls, target services, Live-to-Aurora, installer persistence, recovery, six-case production acceptance, or AP-backed SMP is complete. Production release remains BLOCKED.


## Check/Plan/Do recheck — 2026-10-23

Cross-repository verification on the mirrored runtime branch:

- OctavianOS bounded ingestion, explicit user ELF module smoke, target-routing contracts, and artwork/progress contracts passed on source-fix commit `e946b2336fc905a39618491d7069d5d2128d6ff7`.
- OctavianOS candidate ring-3 matrix run `39849315730` was **cancelled overall**: four candidate jobs passed; Live/BIOS and Live/UEFI were cancelled before completing. Do not call this a six-case pass.
- This repository's workflow-run API still returned no run for `c16306b1fbd8920d2fc360824ac9fe60bc5a8653`; the CPIO-to-RAMFS error-mapping fix and guard remain **not CI-verified here**.

Root cause remains the same lifecycle seam: newc is validated and extracted into an unpublished RAMFS staging tree, but the separate fixed-size VFS has no mount/publication interface and is not backed by that tree. Removing the fail-closed guard would not create filesystem visibility or working file syscalls. The current native syscall surface does not yet provide process-owned descriptors and safe open/read/write/stat operations. The required next work is a capacity-appropriate mount abstraction, atomic root publication with rollback tests, process-bound file syscalls and pointer validation, real target service lifecycles, and then production BIOS/UEFI acceptance plus Aurora, installer persistence, recovery postconditions and real AP-backed SMP.

**Status:** keep PR #187 draft. The guard is a safety barrier, not a fix for the missing rootfs lifecycle. No production ISO publication is authorized until exact-head CI and all production gates pass.


## Source-level rootfs seam correction and latest CI — 2026-10-23

Exact-source review refines the cross-repository diagnosis:

- In OctavianOS's vendored `target_launch.cpp`, the production path checks target/module bounds and then fails closed at `-15`; it does not invoke the CPIO validator, RAMFS extractor, or publisher. Its isolated bounded-ingestion CI pass does not establish launcher integration.
- In the current ChimeraIIOS `kernel/core/target_launch.cpp`, the Live/Recovery path validates/decompresses the archive, stages RAMFS, mounts `/` read-only and `/tmp` writable, and publishes the root pointer only after both mounts succeed. The remaining proof is runtime: the production ISO must show successful mounts and process-originated VFS operations. Installer still fails closed until its storage-backed root namespace exists.
- The current source has a RAMFS root publication path and process-bound read-only OPEN/READ/CLOSE syscalls, plus bounded tmpfs operations for the native init self-test. Source integration and tests do not prove production runtime success. Installer persistence remains a separate disk-backed lifecycle requirement.

The closure work is therefore ordered, not interchangeable: first wire OctavianOS production launcher to validated RAMFS staging (Chimera already has staging); then add atomic root publication with rollback and ownership tests; then process-bound descriptors/syscalls and user-buffer validation; then real target services. Keep the fail-closed guard until those invariants are established.

Latest OctavianOS CI at commit `3d8859714439d307fc6aaafd93930e7b7183dbc5`: bounded ingestion, source integration, target routing, artwork/progress, and explicit ELF smoke passed. Candidate ring-3 run `39866564460` remained in progress; Installer/BIOS and Recovery/UEFI passed as candidate jobs, with four jobs still running at poll time. These are not production ISO results. ChimeraIIOS still returned no workflow run for its recorded source-fix commit, so mirrored source changes remain unverified there.

Release remains blocked pending launcher integration, rootfs publication, real services, six production BIOS/UEFI cases, Aurora, installer cold-reboot persistence, recovery postconditions, and AP-backed concurrent SMP.


## 2026-10-23 follow-up — root causes and closeout boundary

- Verified CI jobs: Boot Artifact Validation #39926508746, Desktop Compatibility #39926508696, Structured ISO #39926646499, and Koronos contracts/build #39925905184 passed. Their logs prove build/structure/source-contract regressions only, not production service readiness.
- The payload-binding regression was a stale source-contract assertion; the test now asserts bounded RAMFS staging, read-only root mount, writable /tmp mount, and delayed root publication. This does not prove successful mounts in a real production boot.
- Source audit still shows a deliberate fail-closed native init: it reports `NATIVE INIT BLOCKED` and exits 78. Installer target launch explicitly refuses launch while the storage-backed root namespace is missing. The three target ELF files being present and structurally valid is not equivalent to target services being operational.
- The production closeout checker requires six target/firmware cases, matching nonzero syscall/readiness PID, rootfs file syscall evidence, Live/Recovery tmpfs mutation traces, display/Aurora, installer persistence, recovery repair, and SMP evidence. The checker does not generate any of that evidence; raw boot artifacts must be collected from real test runs.
- Remaining root causes: production Live service/Aurora session not operationally proven; installer storage namespace/persistence path missing; Recovery repair action/postcondition not proven; AP startup and overlapping multi-CPU execution not proven. Keep release blocked until the unchanged production verifier and all independent runtime gates pass.


## 2026-10-23 follow-up — DAPS CI coverage

- Workflow commit `882caeba2a1a2cfa29c29207818dc1ece40061a2` adds a CI step to compile-check `tools/production-closeout-daps.py` and run `tools/tests/test_production_closeout_daps.py`. This closes a test-discovery gap: the DAPS verifier had regression tests in a separate directory, but the full ISO workflow did not explicitly execute them.
- This verifies the verifier's rejection behavior (missing cases/artifacts, bad ISO digest, path traversal, candidate-smoke substitution), not the production runtime itself.
- The latest DAPS/workflow commits do not yet have a confirmed fresh CI result in this review. The operational blockers remain unchanged: native init intentionally exits 78, Installer lacks a verified storage-backed root/persistence path, and Aurora, recovery repair, six production cases, and AP-backed concurrent SMP require real runtime evidence.


## 2026-10-23 follow-up — raw evidence must agree with claims

- Commits `4ff727634279777420c4ab48cb2f79179dd5d99d` and `badbb57e9f0d3dd9bf6d542b99512b7694d27565` address a further closeout-verifier weakness: the DAPS JSON's booleans and artifact paths were checked, but raw trace contents were not semantically cross-checked against the claimed readiness and service outcomes.
- DAPS now validates the production raw trace for kernel-ready, user-originated target syscall, ring-3 return, target-matched nonzero readiness PID, PID equality, and syscall-before-readiness ordering. It also checks evidence logs for rootfs OPEN/READ/CLOSE, Live/Recovery tmpfs CREATE/WRITE/READ/TRUNCATE, display fallbacks/Aurora, persistence, repair postcondition, and SMP markers.
- Regression tests now cover a readiness claim without a syscall and a raw trace with mismatched PIDs. This tightens the evidence gate; it does not create missing runtime traces or imply that the underlying services work.
- Fresh CI has not yet been confirmed for these commits. Release remains blocked until actual production logs contain the required markers and all six firmware/target cases plus independent gates pass.
