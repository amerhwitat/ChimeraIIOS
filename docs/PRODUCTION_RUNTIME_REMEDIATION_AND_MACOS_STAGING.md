# Production Runtime Remediation and macOS File Staging

Status: implementation plan and acceptance contract; **not evidence that runtime blockers are fixed**.

## Release policy

Keep production release fail-closed. Do not remove the native-init exit-78 blocker or emit target-ready markers until the target's real service manager is running and every required service passes an independent health check. Source inspection, compilation, kernel-ready, a ring-3 syscall acknowledgement, or PID 1 startup alone do not establish production readiness.

## Dependency-ordered implementation

1. **Task execution substrate:** per-task saved CPU/trap context, kernel stack, address-space switching, scheduler state transitions, and isolation tests.
2. **Process lifecycle:** process creation, transactional ELF loading with complete rollback on failure, blocking wait/wakeup, exit-status propagation, and race-safe reaping.
3. **User I/O and storage:** task-owned descriptors, fault-safe user-copy, real ring-3 OPEN/READ/CLOSE tests, writable /tmp, VFS correctness, and durable storage tests.
4. **Init/service supervision:** persistent PID 1, service dependency graph, real child tracking, health checks, restart/failure policy, and readiness derived from observed health.
5. **Target acceptance:** Aurora/Marine session health, installer writes surviving cold reboot, and recovery repair with verified postconditions.
6. **SMP and release matrix:** AP startup and measured overlapping execution on at least two CPUs; immutable, hash-bound Live/Installer/Recovery × BIOS/UEFI traces.

## Evidence required for each production case

- Bind the trace to the exact candidate ISO SHA-256 and production init ELF SHA-256.
- Prove kernel readiness, a user-originated CPL3 syscall acknowledgement, and target readiness from the same real PID where the verifier contract requires it.
- Prove ring-3 file operations and writable /tmp; do not substitute kernel-only helpers or synthetic readiness text.
- Record service health and exit/wait behavior; a PID 1 process that exits is not persistent supervision.
- Live: verify the real Aurora session and display handoff.
- Installer: perform a real write, reboot the VM cold, and verify persistence.
- Recovery: exercise repair and assert the repaired state.
- SMP: capture AP-online evidence and overlapping work on two distinct CPUs; sequential logs do not prove SMP.
- Run all six target/firmware combinations. Preserve logs, artifacts, hashes, and failure details.

## macOS extracted-file staging (not macOS compatibility)

Keep extracted files local and outside public source control unless redistribution rights are confirmed. Prefer redistributable assets and source code. Do not execute or bundle proprietary Mach-O binaries, Apple frameworks, kernel extensions, or macOS system files on the assumption that copying makes them compatible. Native execution needs a compatible loader, ABI/syscalls, libraries, frameworks, and licensing review.

Example WSL copy workflow (edit paths first):

```bash
set -Eeuo pipefail
SOURCE="/mnt/c/tmp/macOS-extracted"
CHIMERA="/mnt/c/tmp/ChimeraIIOS"
OCTAVIAN="/mnt/c/tmp/OctavianOS"
for p in "$SOURCE" "$CHIMERA" "$OCTAVIAN"; do
  [[ -d "$p" ]] || { echo "Missing directory: $p" >&2; exit 1; }
done
for dest in "$CHIMERA/third_party/macos-extracted" "$OCTAVIAN/third_party/macos-extracted"; do
  mkdir -p "$dest"
  rsync -aH --exclude='.DS_Store' --exclude='._*' \
    --exclude='.Spotlight-V100/' --exclude='.Trashes/' "$SOURCE/" "$dest/"
  (cd "$dest" && find . -type f ! -name SHA256SUMS -print0 |
    LC_ALL=C sort -z | xargs -0 -r sha256sum > SHA256SUMS)
done
diff -qr "$CHIMERA/third_party/macos-extracted" "$OCTAVIAN/third_party/macos-extracted"
(cd "$CHIMERA/third_party/macos-extracted" && sha256sum -c SHA256SUMS)
(cd "$OCTAVIAN/third_party/macos-extracted" && sha256sum -c SHA256SUMS)
```

The copy is additive and does not remove stale destination files. Review symlinks, permissions, licenses, and the manifest before committing. Keep proprietary files out of public Git and ISO images unless redistribution is explicitly permitted.

## Completion rule

Mark a stage complete only after its implementation, regression tests, and relevant runtime evidence pass. Record failures honestly and retain the release block until every required acceptance case passes.


## Source audit findings (GitHub main snapshot inspected 2026-10-28)

These findings are source-level observations, not runtime test results:

- `kernel/core/scheduler.cpp` stores a task callback and argument plus metadata, and dispatches callbacks. That is a cooperative callback scheduler; it does not itself establish saved architectural trap contexts, per-task kernel stacks, or an address-space switch.
- `kernel/include/chimera/scheduler.h` explicitly describes `chimera_sched_run_serial_range` as serial stepping and `chimera_sched_run_parallel` as returning zero until AP startup and independent per-CPU workers exist. Do not count serial stepping as SMP evidence.
- `kernel/core/syscall.cpp` explicitly rejects GETPID in the compatibility dispatcher because there is no active process context, and rejects EXIT/EXIT_GROUP because that path has no caller identity or process teardown hook. These are intentionally fail-closed compatibility semantics, not implemented process lifecycle syscalls.
- `kernel/core/process.cpp` maintains process-image records and validates/admit ELF images. Admission metadata alone is not proof of a transactional executable loader that maps pages, switches address spaces, enters user mode, and safely reaps processes.
- Therefore the next code task is not to weaken the release verifier. First identify/implement the architecture trap-frame and context-switch ABI and its per-task memory ownership; then add process-bound syscall context and lifecycle semantics, followed by runtime tests. Keep the exit-78 guard until persistent service supervision and target-specific health checks are real.

## Required implementation PR breakdown

A. Architecture context-switch ABI + per-task kernel stack/address-space ownership and tests.
B. Process-bound syscall context, transactional exec/load, fork semantics, wait queues, wakeup, and reaping tests.
C. Descriptor ownership, fault-safe user memory access, VFS open/read/write/close and writable temporary filesystem tests.
D. PID 1 service supervision, health/dependency state machine, and target-specific readiness.
E. Aurora/Marine runtime health, installer cold-boot persistence, and recovery repair postconditions.
F. AP startup, CPU identity and overlap evidence, then all six immutable target/firmware acceptance traces.

Each PR must build and run relevant tests. Do not combine a source-contract test pass with claims of production acceptance.