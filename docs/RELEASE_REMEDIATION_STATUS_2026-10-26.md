# Release remediation status — 2026-10-26

This file records verified release blockers and a fail-closed remediation order. It is not a release approval.

## Latest observed CI evidence

- ChimeraIIOS workflow run [40058769321](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/40058769321): build, ISO validation, artwork/payload checks, and headless Koronos boot smoke passed; the production userspace handoff gate failed and ISO publication was skipped.
- OctavianOS workflow run [40063838961](https://github.com/amerhwitat/OctavianOS/actions/runs/40063838961): Koronos build and module-classification test passed, but all six target/firmware jobs failed during ISO staging. The Live BIOS log reported that `build/koronos/x86_64/user-init-live.elf` did not exist. The boot/readiness and timeout checks were skipped.

These runs are dated evidence, not a statement about future runs or the current branch head. Re-run CI after changes and link the resulting run IDs here.

## Required sequence

1. Build and validate the actual target init ELF for Live, Installer, and Recovery; verify ELF64, ET_EXEC, executable PT_LOAD, entry-point bounds, and the exact artifact hash before ISO assembly.
2. Build target-specific BIOS and UEFI ISO candidates from those payloads; prove each boot entry selects the correct init and never silently falls back to Live.
3. Execute the real unprivileged init. The CPL3 syscall acknowledgement and target readiness must originate from the same nonzero kernel-owned PID. Keep the existing verifier unchanged.
4. Prove process exit/wait, user-pointer validation, VFS/rootfs mount, read/write/close, writable temporary storage, service supervision, and Aurora handoff with preserved traces.
5. Prove installation with a genuine cold power-off/reboot and verify persistence. Prove recovery with a real repair and checked postconditions.
6. Prove SMP only after AP startup, per-CPU state, synchronization, and overlapping execution of independent tasks on at least two CPUs are measured.
7. Generate a manifest of the exact candidate ISO SHA-256, per-target production init hashes, firmware, QEMU version/arguments, trace hashes, verifier version/results, commit SHA, and artifact provenance for all six cases.
8. Publish a production ISO only if every required gate passes. Showcase and desktop contract tests are useful but cannot substitute for runtime acceptance.

## Desktop/artwork integration

- Preserve checked-in SVG artwork and wallpaper assets as source files; embed or bundle assets only where the build has a reproducible asset pipeline.
- Keep Aurora and Marine web previews distinct from native session launch.
- Catalog entries must distinguish browser preview, source available, compiled, booted, and runtime-verified status.
- Website changes may be published as a showcase independently, but must not imply the operating systems are production-ready.

## Acceptance status

| Gate | Status |
|---|---|
| Native desktop contract and build | Not verified by latest production workflow |
| Koronos build / basic boot smoke | Passed in cited runs |
| Actual init ELF staged into all target ISOs | Failed in OctavianOS run 40063838961 |
| Six production target/firmware boots | Blocked / not verified |
| CPL3 syscall + same-PID readiness | Not established by the cited production run |
| Aurora session handoff | Not verified |
| Installer cold-reboot persistence | Not verified |
| Recovery repair postcondition | Not verified |
| Genuine two-CPU overlapping execution | Not verified |
| Immutable production evidence bundle | Not complete |
| Production ISO release | BLOCKED |

Do not check a gate off because a source file exists, a test image compiles, a synthetic fixture passes, or a browser preview renders. Record the command, exact commit, exit code, target, firmware, and artifact hashes for every acceptance claim.
