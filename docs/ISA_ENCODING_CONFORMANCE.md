# Chimera II R8192 Encoding Conformance Plan

## Scope

This plan establishes the tests required before the illustrative encoding metadata can become a canonical ISA encoding.

## Opcode coverage

- Native opcode namespace: `0x0001..0x011C`.
- Expected semantic instruction count: 284.
- `0x0000` remains available for the explicit NOP convention where implemented.
- Values outside the defined range must produce `InvalidOpcode`.

## Decoder conformance

For each instruction descriptor, verify:

1. opcode bytes decode to the expected mnemonic;
2. destination/source fields decode without truncation;
3. immediate width matches `imm_size`;
4. reserved bits are rejected or normalized according to the future canonical rule;
5. decoded length matches the canonical packet/extension rule;
6. re-encoding the decoded instruction reproduces the canonical byte sequence.

## Privilege conformance

Privileged instructions must return `PrivilegeViolation` when dispatched in user mode. User instructions must remain executable without privileged elevation.

## Service conformance

Recognized OS/device-facing instructions that lack a bound backend must return `UnimplementedService`, not `Executed`. This distinction prevents the research emulator from falsely claiming hardware implementation.

## Timing metadata

`latency` and `throughput` are model metadata. Tests must verify descriptor integrity, not claim physical performance from those values.

## Golden vectors

The supplied `example_binary` values are golden-vector candidates only. They become normative only after the encoding layout is formally frozen.

## Required future test matrix

| Category | Required cases |
|---|---|
| Opcode | every defined opcode + invalid boundary values |
| Registers | low/high register numbers and reserved values |
| Immediate | zero, min, max, sign-extension cases |
| Length | every supported logical instruction length |
| Privilege | user and privileged execution |
| Memory | aligned, unaligned, boundary and fault cases |
| Service | implemented and unimplemented backends |
| Round trip | assemble → encode → decode → re-encode |
| Negative | malformed opcode/field/length combinations |
| Compatibility | semantic registry vs encoding registry |
