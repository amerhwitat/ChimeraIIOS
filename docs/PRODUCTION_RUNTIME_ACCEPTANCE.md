# Production Runtime Acceptance Gate

This document defines the release-blocking evidence required for a production ISO. It is not a statement that the requirements currently pass.

## Required execution evidence

A kernel heartbeat, module registry entry, parsed manifest, load-plan-only ELF admission, candidate probe, or presence of desktop assets is not userspace readiness.

For each production boot, the serial/debug trace must contain these ordered events for the same nonzero PID:

1. `KERNEL_READY`
2. `USER_SYSCALL pid=<N> syscall=<supported-init-ack>` — emitted only after the syscall originates from the running CPL3 init process; kernel-side synthetic markers are forbidden.
3. `USERSPACE_READY target=<live|installer|recovery> pid=<N>` — emitted only after the acknowledgement is validated and the init process is alive.

The verifier must reject missing, duplicated/out-of-order, zero or mismatched PID events, wrong-target events, and markers produced by a candidate/probe executable. Every failure must include the phase, target, firmware mode, and reason. A timeout is a failure, never a pass.

## Mandatory production matrix

Run each case against the exact release-candidate ISO and record artifact SHA-256, commit SHA, firmware configuration, raw serial log, verifier output, and PASS/FAIL/NOT RUN:

| Target | BIOS | UEFI |
|---|---|---|
| Live | Required | Required |
| Installer | Required | Required |
| Recovery | Required | Required |

Do not infer one firmware result from the other. Do not mark unexecuted cases PASS.

## End-to-end checks after userspace starts

- Live: real initramfs init process, user-originated syscall, Aurora/session manager startup, compositor/session handoff, and usable desktop; desktop files alone are insufficient.
- Installer: installer process starts from installer media, discovers supported storage, performs a test installation to a disposable disk, reboots, and boots the installed target.
- Recovery: repair shell starts from recovery media and executes a harmless diagnostic command.
- Storage: write known data, flush, cold power-cycle/restart the VM, reattach the same disk, and verify the data; in-memory or RAM-disk-only tests do not qualify.
- SMP: start application processors using the platform startup protocol, confirm per-CPU identity and scheduler participation, and demonstrate overlapping work on at least two distinct CPUs. A reported CPU count is not proof.
- Mirror parity: repeat the same checks against the OctavianOS source and its own production-built ISO. Upstream results cannot stand in for OctavianOS evidence.

## Implementation dependencies (must be real, not mocked)

1. ELF loader: validate headers and arithmetic; map PT_LOAD pages; copy file bytes; zero BSS; enforce segment permissions and NX/W^X; handle mapping failures safely.
2. Process address spaces: preserve required kernel mappings while providing isolated user mappings, a valid user stack, and cleanup on exit/fault.
3. x86-64 privilege transition: correct GDT/TSS/RSP0 setup, ring-3 entry, syscall/interrupt entry and safe return, plus user-fault diagnostics.
4. Target selection: exactly one explicit Live/Installer/Recovery target; require its matching init executable and dependencies; fail closed if absent or inconsistent.
5. Runtime services: register real block-device backends, mount persistent storage, and only report services RUNNING after start callbacks and independent health checks succeed.
6. SMP: AP trampoline/startup, per-CPU state and stacks, synchronization, scheduler dispatch and concurrency tests.

## Release rule

The gate passes only if all six firmware/target combinations and all applicable end-to-end checks pass on the exact artifacts intended for publication. Keep release publication blocked on any FAIL or NOT RUN. Store logs and artifact hashes with the CI run. Never synthesize success markers or weaken this gate to obtain a green dashboard.
