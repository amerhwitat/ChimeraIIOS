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
