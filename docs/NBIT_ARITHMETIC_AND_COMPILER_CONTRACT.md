# Chimera N-bit arithmetic and compiler contract

## Scope

Chimera's N-bit model is width-parametric: N is a positive bit count, not a
single fixed machine word. This specification allows operands and destinations
to have different widths (for example, 257-bit + 8193-bit -> 9000-bit). Widths
are explicit in IR and must not be inferred from the host compiler's `long`.

The reference evaluator is `tools/math/chimera_nbit.py`. It covers arbitrary-
precision integer add/subtract/multiply/divide/remainder, bitwise operations,
shifts, comparisons, signed/unsigned interpretation, result truncation, and a
host-side Decimal floating arithmetic model.

## Typed IR / source language direction

- `iN`: N-bit integer bit-vector, with explicit signedness at operations.
- `uN`: unsigned N-bit integer.
- `fN`: floating format with a separately specified encoding, exponent width,
  significand width, rounding mode, subnormal and exception behavior. Do not
  equate decimal precision with an IEEE binary format.
- `qN.F`: fixed-point bit-vector with N total bits and F fractional bits.
- `bool`: canonical 0/1 logical value.
- Constants carry exact width/type: `const i8193 0x...`, `const f256 1.25`.
- Variable-width operations use explicit destination width and extension rule:
  `add i9000, i257, i8193, signed=0, overflow=wrap`.

## Required lowering rules

1. Preserve source widths and signedness through parsing, optimization, debug
   information, and object metadata.
2. Define overflow per operation: wrap, trap, saturate, or report flags.
3. Define divide-by-zero, signed-min/-1 division, shifts >= operand width,
   carry/borrow, comparisons, and conversion semantics.
4. Lower native-supported widths to ISA instructions; lower other widths to
   multi-limb sequences or runtime helpers. Never silently narrow to host width.
5. Define floating formats by exact bit layout and IEEE-754 behavior before
   claiming bit-exact FPU support. The current Python Decimal model is a
   high-precision reference, not an IEEE-754 emulator.
6. Assemblers/disassemblers must preserve width/type suffixes and pseudo-op
   expansion; debuggers must show exact-width hex, signed/unsigned decimal,
   floating interpretation, and flags.
7. Conformance requires tests for boundaries around 1, native register width,
   64, 128, 256, 8192, and mixed widths; randomized differential testing; and
   official ISA tests for any hardware backend.

## Status

This is a host-side reference foundation and language/IR contract. It does not
by itself add arbitrary-width physical registers to x86-64/ARM/RISC-V hardware,
nor does it mean the existing C/C++ compilers, assemblers, disassemblers, FPU,
debugger, or kernel have completed integration. Those require staged backend
and ABI work and conformance tests.
