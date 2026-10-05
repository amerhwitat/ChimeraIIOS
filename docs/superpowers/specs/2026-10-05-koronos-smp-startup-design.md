# Koronos SMP startup and dependency-aware boot design

Status: proposed design for review  
Repository: `amerhwitat/ChimeraIIOS`  
Target base: `main`

## Goal

Reduce measured time to a usable kernel and Aurora desktop by making safe startup work genuinely concurrent where dependencies permit it, while keeping correctness and a bounded single-core fallback. Report which work runs serially, concurrently, or after the interactive desktop is ready.

The current source detects logical CPU count but brings only CPU 0 online. The runtime loop dispatches only on CPU 0; the `chimera_sched_run_parallel` helper iterates CPUs serially; and `kernel/core/parallel.cpp` partitions work but executes it on one thread. Service startup resolves dependencies to a linear order. The Koronos build script also compiles its inputs in serial loops. The design must start from this state and retain the recent task-dispatch fixes in `main`.

The repository also contains `Mobile Microkernel` (ARM64 and RISC-V contracts), a Mobile Edition runtime, and mobile sync/validation manifests. Shared scheduler and service-graph behavior must be reflected in those targets; x86_64 AP startup code cannot be copied into a different architecture and described as working.

## Proposed boot model

### CPU discovery and bring-up

Keep separate counts for detected and online CPUs. Add an x86_64 AP startup path with per-CPU state/stacks, a bounded startup handshake, and explicit failure reporting. Do not advertise a CPU as online until it has entered the scheduler safely. Start with the BSP; attempt AP startup under a timeout. If all APs fail or multiprocessor mode is disabled, continue in the current single-core mode without hanging boot.

Use a release/acquire readiness barrier before workers accept tasks. Define who owns scheduler queue operations and synchronization on every core. Never run one scheduled task twice if a wakeup, timeout, or failed AP startup races with dispatch. Do not extend AP support to another architecture until that architecture has its own implementation and tests.

### Task and service execution

Preserve the current scheduler task contracts and priorities. Extend task metadata with dependency IDs and explicit execution eligibility (boot-critical, parallel-safe, optional, or deferred). Validate the dependency graph and report missing dependencies/cycles before starting dependent services.

Keep the minimum boot chain ordered: firmware/platform discovery, memory and interrupt setup, scheduler readiness, required storage/root selection, required drivers, required system services, then Aurora session launch. Start independent, explicitly parallel-safe services concurrently only after their shared prerequisites are ready. Keep optional services and noncritical initialization after the desktop becomes usable. A failed optional task is reported and isolated; a failed required dependency follows the existing recovery policy rather than releasing downstream tasks.

The existing boot-phase manifest and measurement policy remain the source of stage names and required stage order. Add dependency/eligibility data without changing signed/measured payload expectations unintentionally.

### Build-time parallelism

Make `tools/build-koronos.sh` compile independent translation units concurrently with a bounded job count, deterministic object names, and clear per-file diagnostics. Preserve a serial mode and compare serial and parallel outputs at the required symbol/ELF validation level. Keep build-time parallelism distinct from runtime SMP; one does not prove the other works.

### Measurements and Aurora readiness

Add stage timings for BSP/AP startup, scheduler readiness, required services, deferred services, and Aurora readiness, using a monotonic clock and avoiding ROM/media enumeration. Keep the existing measurement policy's required sequence and recovery behavior. Report cold/warm boot runs, CPU count, and task/service critical path so optimization claims are reproducible. Do not mark the desktop ready before required input, graphics, session, and shell prerequisites pass.

### Microkernel and Mobile Edition alignment

- Put portable dependency, eligibility, status, and measurement contracts in shared headers/manifests only where both runtimes can honor them.
- Implement CPU bring-up per architecture. The first native SMP implementation is x86_64; ARM64/RISC-V Mobile Microkernel support is a separate architecture-specific port with its own startup protocol and tests.
- Update `Mobile Microkernel` scheduler/service contracts, `mobile/mobile-sync.json`, Mobile Edition runtime targets, and CI together when shared semantics change. Clearly report architecture targets that remain single-core or not yet implemented.
- Keep AP startup, parallel task queues, and service scheduling out of Aurora UI code; Aurora consumes readiness/measurement state from the runtime.

## Acceptance criteria

- CPU counts distinguish detected from online processors; online count remains one when AP startup is unavailable or fails.
- QEMU x86_64 boot with 1, 2, and 4 CPUs completes without hangs; injected AP timeout/failure continues via BSP fallback.
- Scheduler tests prove eligible independent tasks overlap on separate worker contexts, each task runs at most once, dependencies are respected, and failure/cancellation does not release blocked dependents.
- Service DAG tests cover cycle/missing-dependency diagnostics and optional versus required failure behavior.
- Boot-stage measurements preserve existing required stage order and include a usable Aurora readiness marker.
- Serial and parallel kernel builds pass the same ELF, required-symbol, and note validation; a failed compile identifies its source and prevents linking incomplete objects.
- CI runs the existing scheduler runtime tests plus the new SMP/service graph tests, with a QEMU SMP job where the current runner supports it. Unsupported environments must be explicit.
- Compare boot timing against a recorded baseline; do not claim a speedup unless repeated comparable measurements show one without correctness regressions.
- Mobile sync and validation jobs prove the shared scheduler/service contracts match their edition-specific implementations; no x86-only result is presented as ARM64 or RISC-V SMP coverage.

## Out of scope

- Parallelizing dependent service work or making all boot phases asynchronous.
- Unbounded worker/task queues, blocking boot indefinitely on an AP, or hiding failed optional services.
- Changing firmware trust, measured-boot hashes, or recovery semantics without updating and validating the corresponding policy.
- Running ROM discovery, hash scans, MAME metadata queries, or emulator builds during boot/login.
- Claiming all mobile architectures are SMP-enabled based only on x86_64 QEMU coverage.

