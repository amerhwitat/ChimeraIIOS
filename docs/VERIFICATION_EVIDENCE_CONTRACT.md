# Verification Evidence Contract

This document defines the evidence required before describing a Chimera II OS capability as implemented, supported, or release-ready. Use it in code review, CI, release notes, and the output of `build-chimera-iso.sh`.

## Non-equivalences (mandatory)

- **Documented is not implemented.** A design, ABI, README statement, schema, or TODO is documentation until executable code and tests establish behavior.
- **Cataloged is not executable.** An ISA/driver/filesystem/application registry entry or discovered upstream source is inventory metadata. Execution support requires a real decoder/encoder or loader, semantic behavior, ABI integration where relevant, and tests.
- **Compiled is not booted.** A successful compiler/linker exit proves that an artifact was produced, not that firmware or a bootloader can load and run it.
- **Booted is not userspace-ready.** Reaching kernel entry, printing a banner, discovering modules, queuing an ELF, or entering a scheduler does not prove a user process entered ring 3 / the architecture's unprivileged level and made progress.
- **Sequential multi-CPU simulation is not genuine SMP.** Iterating over CPU IDs on one execution stream is not concurrent execution. Genuine SMP evidence requires AP/secondary-CPU startup, per-CPU scheduler and interrupt state, architecture context switching, synchronization safety, and observable overlapping task progress on at least two CPUs.

These are separate evidence levels, not synonyms. A claim at one level must not imply a higher level.

## Capability evidence levels

| Level | Minimum evidence | Does not establish |
|---|---|---|
| L0 — Documented | Design/specification and explicit scope | Implementation |
| L1 — Cataloged | Validated registry/schema row with provenance | Executable behavior |
| L2 — Implemented | Code path is linked/reachable and focused tests exercise behavior | Full architecture conformance |
| L3 — Compiled | Reproducible build produces the named artifact | Bootability |
| L4 — Booted | Automated emulator or hardware evidence reaches a named boot milestone | Userspace execution |
| L5 — Userspace-ready | Real loader/privilege transition, user entry, syscall/ABI smoke test, and observable task progress | General application compatibility |
| L6 — Conformance-tested | Relevant normative test suite and documented coverage/results | Untested extensions or other hardware |
| L7 — SMP-verified | At least two CPUs online and independent tasks demonstrably progress concurrently, with per-CPU state and synchronization tests | Scaling, stress, or physical-hardware support beyond tested targets |

A project feature can have different levels for different targets. Report evidence per architecture, edition, firmware path, and backend; do not promote a whole subsystem based on one target's test.

## Koronos ELF and SMP acceptance

Do not wire a generic ELF loader into the production boot path until the x86-64 backend supplies and tests all of the following:

1. User page-table mappings, safe splitting of existing large identity mappings, kernel aliases, hardware NX/W^X permissions, and required TLB invalidation.
2. User GDT descriptors, TSS, per-CPU interrupt/exception stacks, and audited privilege-return entry (for example, a correct IRETQ/SYSRETQ path).
3. Transactional ELF segment mapping, zero-filled BSS, guarded user stack, rollback on every failure, and a controlled user entry.
4. A syscall/ABI smoke test from unprivileged mode that returns observable output or status.
5. APIC discovery and secondary CPU startup, per-CPU scheduler/interrupt state, assembly context switching, synchronization tests, and a QEMU run showing simultaneous progress on at least two CPUs.

Host-side ELF parsing, a generic loader callback test, a Multiboot2 kernel build, or a scheduler loop that visits multiple CPU structures is useful evidence for its own level only; none substitutes for the above.

## ISA and compatibility claims

For each ISA family/instruction, distinguish at minimum: `documented`, `cataloged`, `encoding-verified`, `decoded`, `executed`, and `conformance-tested`. Keep normative source/version, encoding fields, operand constraints, effects, exceptions, and tests linked to each verified form. Unknown or malformed encodings must fail closed. Semantic-IR plans, discovered TableGen identifiers, example hex strings, and translation profiles are not machine-code execution or compatibility proof.

For foreign applications, separately record file-format recognition, loader support, instruction execution backend, ABI/syscall coverage, libraries, graphics/runtime integration, and test evidence. A recognized PE/ELF/Mach-O file is not proof that it can run.

## Builder and CI requirements

The canonical integration entry point remains `./build-chimera-iso.sh`; invoke it with Bash, not `sh`. The builder and CI should run the relevant static, unit, kernel, boot-artifact, ISO, and emulator acceptance checks and fail closed when a required gate fails. Optional online catalog research must remain separate from required deterministic validation.

Recommended local sequence from the repository root:

```bash
bash -n build-chimera-iso.sh
find . -type f -name '*.sh' -not -path './.git/*' -print0 | xargs -0 -r -n1 bash -n
python3 -m compileall -q tools tests
# Run repository-defined unit/static checks and ISA database validators.
# Then build the kernel and verify the boot format:
./kernel/build-koronos.sh
grub-file --is-x86-multiboot2 build/koronos/koronos.elf
# Finally run the canonical ISO builder and the documented QEMU gates:
./build-chimera-iso.sh
```

These commands are a checklist, not a claim that they passed in this documentation change. Use the repository's actual artifact paths if a build profile changes them; do not let a missing artifact silently count as a pass. Record command, exit status, commit SHA, target/profile, and artifact hashes in CI or release evidence.

## Release reporting template

For each release candidate, publish:

- **Documented:** links to specification and limitations.
- **Implemented:** code paths and focused tests.
- **Compiled:** build job, target, compiler/toolchain, artifact hash.
- **Booted:** emulator/firmware, boot milestone, log/artifact.
- **Userspace-ready:** unprivileged process entry, ABI smoke test, observed progress.
- **Conformance-tested:** suite/version, tests run/passed/skipped, known gaps.
- **SMP-verified:** CPU count online, context-switch/concurrency evidence, race/synchronization tests.

Use `not implemented`, `not tested`, or `blocked` explicitly when evidence is absent. Do not replace missing evidence with aspirational wording.
