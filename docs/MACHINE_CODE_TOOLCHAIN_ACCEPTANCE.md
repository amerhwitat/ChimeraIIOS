# Machine-code identification and toolchain acceptance

## Current implementation boundary

`tools/machine-code/identify.py` identifies container formats and architecture hints from ELF, PE/COFF, DOS MZ, Mach-O (including fat/universal containers), and WebAssembly signatures. It reports unknown or truncated inputs conservatively and emits JSON. Run it with:

```sh
python3 tools/machine-code/identify.py path/to/program
python3 tools/machine-code/test_identify.py
```

This is the first input-identification stage only. A file signature or architecture tag is not proof that its instructions decode, that the binary is safe, or that an execution provider is installed. Raw machine code has no universal self-describing architecture; it needs an explicit target/profile or independently validated decoder. The current tool does not disassemble, assemble, compile, emulate, or execute code.

## Required shared toolchain shape

All frontends should converge on one explicit target description and machine-code artifact contract:

1. **Identify / validate container:** format, class, byte order, ABI, machine ID, extensions, entry points and bounds.
2. **Decode:** target-specific decoder returns instruction length, opcode/encoding fields, typed operands, implicit register/memory reads and writes, flags, privilege, exceptions and confidence/provenance.
3. **Normalize:** architecture-neutral IR preserves width, signedness, endianness, memory ordering, traps and control flow. Never silently erase architecture-specific semantics.
4. **Assemble / encode:** instruction forms are selected by a versioned target profile; reject invalid operand combinations, reserved bits and out-of-range immediates rather than truncating.
5. **Compile / lower / link:** compiler selects a concrete, implemented backend. Logical N-bit arithmetic is not evidence of a physical N-bit processor backend.
6. **Execute / emulate:** dispatch only to an installed provider whose target, ABI and feature set match. Fail closed if no provider matches.
7. **Verify:** round-trip encode/decode tests, golden encodings, invalid-encoding tests, differential execution against a reference implementation, normative ISA suites, ABI tests and target-specific runtime evidence.

## Per-ISA coverage ledger

Track each architecture and extension independently using these statuses: `cataloged`, `decoded`, `encoded`, `semantic-modelled`, `executed`, `differential-tested`, `official-conformance-tested`. Each row must include ISA revision, enabled extensions, source citation/revision, test-suite version, tested instruction count, excluded forms, known gaps, and reproducible CI artifact. A candidate row or worked example is not complete coverage.

## Execution-provider boundaries

- **Windows:** PE identification is not Windows API/NT ABI compatibility. Use a native host provider or a specifically implemented compatibility layer; document APIs and system-call coverage.
- **macOS:** Mach-O identification is not Darwin syscall, framework, code-signing, or entitlement compatibility. Native execution must remain on supported Apple hosts; any translation path needs explicit validation.
- **DOS:** DOS MZ detection does not establish real-mode or protected-mode execution. DOSBox/DOSBox-X adapters must confine paths and declare CPU mode, DPMI and device limitations.
- **Other Linux architectures:** ELF `e_machine` is routing metadata. Require a matching native CPU or installed emulator/translator, a compatible ABI/sysroot, and execution tests.
- **Emulators:** provider discovery, installed status, accepted formats, target coverage and successful smoke-test evidence are separate fields. Do not label a provider verified merely because its executable name is found.

## Koronos and ISO release gates

Do not connect ELF loading to the production boot path until page-table management, W^X/NX, kernel aliases, TLB invalidation, GDT/TSS and per-CPU interrupt stacks, audited privilege return, user stack/ABI and a ring-3 syscall/progress smoke test are validated. Installer/live/recovery module discovery is not equivalent to launching each userspace target. Genuine SMP requires AP startup, per-CPU scheduler and interrupt state, concurrent context switching, safe synchronization, and measured overlapping progress on at least two CPUs.

For each release, publish separate evidence for BIOS and UEFI, each advertised architecture, live, installer, recovery and diagnostics targets, and each supported vCPU topology. An ISO mastering success alone is not boot evidence. Keep unsupported target choices visibly unavailable rather than falling through to another architecture's kernel.

## Test status for this change

The focused regression suite covers representative format signatures, endianness, DOS-versus-PE distinction, truncated headers and conservative unknown handling. It does not establish exhaustive machine-code identification, instruction conformance, OS compatibility, ring-3 readiness, SMP, or ISO bootability.
