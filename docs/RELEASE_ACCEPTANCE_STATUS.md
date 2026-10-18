# Release acceptance status

This file separates evidence from roadmap claims. A boot probe is not a completed installer, repair workflow, desktop launch, or release.

## Implemented and locally/CI exercised

- [x] Source-backed RISC-V encoding import: 1,459 records from 141 source files; zero fetch failures in the import workflow.
- [x] Universal ISA catalog generation: 1,613 forms across 15 architecture identifiers.
- [x] Native command candidate inventory with explicit native allowlist vs deferred candidates.
- [x] Trainable character-level RNN language model: BPTT training, serialized weights, scoring, round-trip tests, and training loss reduced in CI. This is a small RNN language model, not an LLM-scale foundation model.
- [x] RNN scores only reorder advisory candidates. They do not authorize native command execution or mark ISA forms implemented.
- [x] Standalone Live, Installer, and Recovery user-init ELF probes pass the existing BIOS/UEFI matrix.
- [x] Kernel address-space self-test reports user U/RW/NX permissions and reclaimed frames in the userspace acceptance path.

## Current full-ISO acceptance

The current change stages the per-target user-init ELF files into the ISO and passes them through GRUB as Multiboot2 modules. The boot menu now sets an explicit `chm.target` for Live, Installer, and Recovery. The current full-ISO QEMU jobs are re-running against these changes; only their latest successful run should be treated as evidence.

A passing user-init probe must include all of:
- `KORONOS READY`
- `USERSPACE READY: <target> init pid=1` emitted by ring-3 userspace
- syscall return to ring 3
- the process page-table permission self-test
- clean init-probe exit

## Still release-blocking

- [ ] Real Installer userspace writes to a disposable virtual disk, reports the install result, and the installed image boots.
- [ ] Recovery userspace performs and verifies an actual repair operation on a disposable damaged filesystem/image.
- [ ] Aurora compositor/desktop is launched by userspace and produces a distinct `AURORA READY` marker in full-ISO QEMU evidence.
- [ ] Genuine concurrent execution on multiple CPUs with per-CPU scheduler/context evidence; sequential simulation does not count.
- [ ] Per-instruction decoder/interpreter implementation and architecture-appropriate conformance tests. The imported ISA forms are catalog entries, not proof of execution support.
- [ ] Application-by-application Python/Java ports, feature-parity tests, GUI packaging, and release artifacts across the eligible repositories.

Do not publish a stable OS release while any release-blocking gate remains unchecked. Do not downgrade a failing gate to a warning merely to make CI green.
