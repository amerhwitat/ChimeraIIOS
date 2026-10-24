# Runtime blocker audit — 2026-10-24

## Scope and evidence

This report records the latest OctavianOS candidate run, [#40046486286](https://github.com/amerhwitat/OctavianOS/actions/runs/40046486286), at head `c6221763db7f56b7b9d302383f1f9e2580633bc4`. All six candidate jobs completed successfully. Their logs are smoke-test evidence only and are not the six-case production DAPS matrix.

The candidate logs include these explicit runtime facts:
- `[ARCH] ... user-image launch remains gated on target payload acceptance`
- `[SCH] Online scheduler CPUs: 1 (AP startup not implemented)`
- `[DRV] Native/compatible bindings: 0` and `[DRV] Active driver set: 0`
- `[KORE] Storage/device/security services BLOCKED pending implementation health checks`
- `[KORE] Registry initialized; service registration is not service readiness`
- `[INST] Installer target not selected: no installer modules`
- `[REC] Recovery target not selected: no recovery initramfs module`
- `[MON] Runnable: 0` after the one-shot user probe exits.

The installer probe log does show a user-originated syscall acknowledgement, `USER INIT SYSCALL: target=installer init_pid=1`, followed by generic `USERSPACE READY: installer init pid=1` and a clean exit. That is not proof of a working installer: no installer modules were selected, no storage-backed installer root was demonstrated, and no persistent write/cold reboot/readback occurred. Live and Recovery have the same probe-vs-service distinction. The candidate timeout log correctly shows the non-returning ring-3 probe being aborted at the kernel deadline.

## Root cause

The target launcher is still a synchronous single-init probe/launch path. `kernel/core/process.cpp` is a bounded ELF admission/state registry; it does not create independently scheduled process execution contexts or provide production spawn/wait/reap. The scheduler currently schedules callbacks; `chimera_sched_run_parallel` deliberately returns zero because AP workers are not started. The kernel log explicitly confirms only one CPU online. Thus the existing supervisor callbacks cannot yet be wired to honest, independent service processes.

The release verifier in `tools/production-closeout-daps.py` correctly requires the target-specific production marker:
- Live: `USERSPACE TARGET READY: live component=aurora-session init pid=N`
- Installer: `USERSPACE TARGET READY: installer component=install-executor init pid=N`
- Recovery: `USERSPACE TARGET READY: recovery component=recovery-runtime init pid=N`

It also requires the user-originated syscall PID to match, the marker order to be correct, and each trace to contain the same verified production ISO SHA-256 binding. Generic `USERSPACE READY` smoke markers are insufficient. Do not weaken this verifier.

## Plan / do / check / act — next non-skippable gates

1. **Plan:** specify process ownership, per-process page tables and saved register contexts, kernel/user stacks, scheduler transitions, syscall ABI for spawn/wait/exit, child ownership, zombie/reap semantics, synchronization and rollback.
2. **Do:** implement context switching and syscall lifecycle as one coherent kernel change; add unit tests for state transitions, PID non-reuse, parent/child wait, exit status, fault/timeout cleanup, address-space destruction, and resource exhaustion.
3. **Check:** run kernel build, regression tests, then QEMU tests proving two independently scheduled processes and successful wait/reap. A single probe ELF or sequential callbacks do not count.
4. **Act:** fix every failure without changing acceptance assertions; rerun the affected gates and retain logs.
5. Implement and test a production service backend against those real process APIs; add separate Live, Installer, Recovery and installed-desktop manifests.
6. Implement real device/storage, filesystem, IPC, logging, input/display, session, and recovery services. Require Aurora/Marine session handshake, installer durable write/sync/cold reboot/readback, and bounded recovery repair with verified before/after state.
7. Start APs and capture overlapping work on at least two distinct CPU IDs. Sequential calls to a scheduler function are not SMP evidence.
8. Build one final ISO; capture six actual Live/Installer/Recovery × BIOS/UEFI traces, stamp the launched ISO SHA-256 into each trace, and run the unchanged production DAPS verifier against those exact artifacts.

## Current decision

- Candidate smoke matrix: **6/6 jobs passed**, at the pinned candidate head above.
- Real multi-process lifecycle: **NOT IMPLEMENTED / NOT PROVEN**.
- Production service backend and target manifests exercised by real processes: **NOT PROVEN**.
- Aurora/Marine, installer persistence, recovery postcondition: **NOT PROVEN**.
- AP-backed SMP: **NOT IMPLEMENTED**.
- Six hash-bound production traces passing unchanged DAPS: **NOT ESTABLISHED**.
- Production release/publication: **BLOCKED**.

This audit is deliberately fail-closed. It records observed evidence and does not convert candidate smoke results into production acceptance.
