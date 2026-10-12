# Capability evidence, acceptance gates, and real SMP

## Mandatory language

Every capability must be described using an evidence-backed status. These statements are engineering requirements, not slogans:

1. **Documented is not implemented.** A specification, roadmap, API catalog, or source reference establishes intent only.
2. **Cataloged is not executable.** A row in an ISA, language, package, terminal, or compatibility registry is not proof of a working decoder, compiler, runtime, or command.
3. **Compiled is not booted.** A successful compiler/linker exit proves only that a particular source revision produced an artifact for a stated target.
4. **Booted is not userspace-ready.** Reaching an early kernel message does not prove a working root filesystem, init/service manager, shell, storage, networking, login, installer, or Aurora session.
5. **A sequential multi-CPU simulation is not genuine SMP.** Running CPU objects one after another, testing a scheduler with mocked CPUs, or printing multiple CPU identifiers is not symmetric multiprocessing.

The machine-readable registry is docs/validation/capability-evidence.json. Validate it with:

    python3 tools/validation/validate_capability_status.py

The validator checks status vocabulary, evidence references, required promotion rules, and the explicit no-simulation-as-SMP rule. It cannot itself prove that evidence claims are true; CI artifacts, logs, target identities, and review must support them.

## Status vocabulary

- **documented**: an explicit written contract exists.
- **cataloged**: metadata has been recorded; execution is not implied.
- **implemented**: code for the named scope exists; test evidence is still required before stronger claims.
- **compiled**: a specified build command succeeded and produced an identified artifact.
- **booted**: a named image or target reached a named boot milestone with a retained log.
- **userspace-ready**: the declared userspace acceptance suite passed on that image.
- **conformance-tested**: a named conformance suite passed on the recorded revision without skipping required cases.
- **partial**: a limited implementation exists and the stated gaps remain.
- **planned**: intended work without verified implementation.
- **not-verified**: no sufficient evidence supports a stronger status.
- **not-implemented**: an implementation is known to be absent for the declared scope.

Statuses apply to the exact scope and target named in the record. A host-side prototype cannot promote a bare-metal target. A cross-compiled object cannot promote a runtime. A single QEMU configuration cannot promote all hardware.

## Required acceptance ladder

    documented → cataloged → implemented → compiled → booted
               → userspace-ready → conformance-tested

This ladder is not automatic. Each transition requires evidence appropriate to the capability. A status may remain partial, planned, or not-verified even if earlier artifacts exist.

### Build and ISO

The root builder is build-chimera-iso.sh. It builds the ISO and validates its structure; use tools/build/orchestrator.py all for the native CMake build, registered language projects, tests, and packaging. CI must run both paths when the change affects their respective scope. Logs and checksums identify the actual artifact; an ISO mastering success alone does not establish a successful boot.

### Boot and userspace

Record at least the commit SHA, ISO checksum, machine/emulator configuration, serial log, and last confirmed milestone. Separate:
- firmware/bootloader handoff;
- Koronos entry and early initialization;
- rootfs/init/service-manager start;
- shell and storage readiness;
- network readiness when claimed;
- Aurora desktop interactive readiness;
- installer partition/format/install/reboot readiness.

If the CI workflow only checks boot messages or static files, report that limited milestone, not userspace-ready.

### Real SMP acceptance

Do not mark real-smp as implemented, compiled, booted, userspace-ready, or conformance-tested merely because a sequential CPU simulation or a mocked scheduler passes.

A real-SMP promotion requires all of:
- at least two independently executing hardware or virtual CPUs;
- evidence that secondary processors are started and acknowledged by the boot path;
- concurrent work demonstrably running on different CPUs (per-CPU identity and synchronization);
- inter-processor interrupt and cross-CPU wakeup coverage where the platform uses them;
- lock/atomic/barrier and shared-data stress tests;
- repeatable test logs and the exact tested architecture/emulator/hardware configuration.

Until these gates pass, keep SMP not-verified and describe CPU simulation as simulation.

## Change-control rules

- Keep source code, generated artifacts, documentation, and acceptance tests consistent.
- The ISO builder validates this registry before performing expensive build work and stages the registry and this guide into the installed documentation.
- A new feature must add or update its registry entry and tests in the same change.
- Do not rewrite status based on roadmap language or catalog size.
- Never convert skipped tests into passed tests; report skips and unsupported targets explicitly.
- Do not claim every repository file is compiled: documentation and data files are validated and staged; only source files selected by a defined build target are compiled.

## Current declared boundaries

The registry deliberately keeps native VFS-backed syscalls, complete foreign OS ABIs, full macOS app compatibility, a native Chimera .NET runtime, complete live userspace readiness, and genuine SMP at partial/planned/not-verified status until their specific evidence gates pass.
