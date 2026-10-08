# N-bit toolchain integration status and contracts

## Portable typed IR

`tools/math/chimera_toolchain.py` defines a width-aware typed instruction IR,
a textual pseudo-assembler, JSON IR object, canonical disassembler output,
debug formatting, and target-aware lowering plans. Widths and signedness survive
serialization. Integer types are `iN` / `uN`; floating types are `fN`;
fixed point is `qN.F`; booleans are one bit. Example:

```asm
add u9000, u257, u8193 overflow=wrap
mul i8193, i8193, i8193 overflow=trap
fdiv f256, f256, f256 overflow=flags
```

The actual grammar uses explicit register/type pairs:
`add result:u9000, lhs:u257, rhs:u8193 overflow=wrap`.

## Lowering

Target plans cover x86-64, AArch64, ARM32, RV32/RV64, MIPS32, and Power64.
Native-width operations are represented as target-qualified instruction plans.
Non-native widths lower to named multi-limb runtime-helper calls. These are
lowering contracts, not machine code emission; each real backend still needs
ABI-correct helper implementations, register allocation, relocation/object
integration, and execution tests.

## Floating point contract

Do not define arbitrary `fN` as “N-bit IEEE-754”. A floating format must specify
sign/exponent/fraction bit layout, bias, quiet/signaling NaNs, infinities,
subnormals, signed zero, rounding modes (nearest-even, toward-zero, toward
positive/negative), exception flags (invalid, divide-by-zero, overflow,
underflow, inexact), fused operations, conversions, and tininess detection.
IEEE binary32/binary64 can be used where a host implementation has a verified
bit-exact path. Other formats require a format-specific soft-float implementation
and conformance vectors. Decimal arithmetic is not a substitute for that.

## Native compiler/linker/debugger integration

The IR JSON schema is suitable as an interchange boundary for compiler front
ends, assemblers, linkers, disassemblers and debuggers. Object files should
store a versioned `CHIR-NIR` metadata section with type widths, signedness,
overflow policy, helper ABI version, and source locations. Linkers must reject
incompatible helper ABI versions. Debuggers should render exact-width hex and
signed/unsigned interpretations. Decompilers should reconstruct explicit width
annotations and indicate when source semantics are ambiguous.

## Conformance gates

- Unit tests and randomized differential checks against Python integers for
  integer arithmetic, including widths 1, 7, 8, 31, 32, 64, 65, 128, 256,
  8193, and mixed operand/result widths.
- Integer corner cases: zero division, min/-1, shifts >= width, signed/unsigned
  compare, carry/borrow, overflow policies, truncation/extension.
- IEEE binary32/binary64 vectors and format-specific tests for any soft-float.
- Official architecture suites (RISC-V architectural tests; Arm Architecture
  tests where licensed/available; x86 vendor/system test suites; MIPS/Power
  architecture tests) for native hardware backends.
- No backend is marked conformant until the tests run and results are archived.

## Honest implementation status

The portable IR, pseudo-assembler/disassembler, debugger formatting and lowering
plan are reference tooling. This change does not silently replace the existing
native compiler, linker, kernel, or architecture-specific assembler, and does
not claim a full native backend, arbitrary-width physical registers, IEEE
bit-exact fN, or ISA conformance without implementation and test evidence.
