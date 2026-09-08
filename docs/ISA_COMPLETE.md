# Chimera II ISA Integration

## Scope

Chimera II now exposes a unified ISA abstraction for the experimental 8192-bit machine plus interoperability-oriented decoders for RV32I/RV64I, AArch64 and x86-64. This is an architectural integration layer, not a claim that Chimera implements every instruction of every external ISA.

RISC-V is an open standard with a small base ISA plus optional extensions. The ratified specification explicitly separates base integer ISAs from extensions and includes privileged architecture, vector, bit-manipulation and cryptography families. See https://docs.riscv.org/ and https://github.com/riscv/riscv-isa-manual .

x86-64 is a CISC ISA. Intel publishes the complete architecture and instruction references in its Software Developer Manuals. Chimera uses those public specifications as interoperability references but does not copy their copyrighted instruction tables into this repository. See https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html .

AArch64 is included as a second RISC-family compatibility target; Arm publishes machine-readable and human-readable instruction descriptions through its architecture documentation.

## Chimera execution layers

1. **Frontend**: fetch, length classification, ISA-family selection.
2. **Decoder**: family-specific decode into `chimera::isa::Instruction`.
3. **IR**: normalized opcode class, registers, immediate and memory effects.
4. **8192-bit execution**: RegisterN/CPU8192 backend.
5. **Kernel boundary**: traps, syscalls, scheduling, virtual memory, IPC and I/O.
6. **Aurora**: GPU/Wayland rendering and presentation.

## Implementation status

- RV32I/RV64I common integer/load-store/branch/system/atomic classes: implemented decoder skeleton.
- x86-64 common control/system/data movement classes: implemented decoder skeleton.
- AArch64 common branch/system/load/store/integer classes: implemented decoder skeleton.
- Full external-ISA compatibility: **not yet complete**; extension-by-extension conformance tests are required.
- Chimera-8192 native ISA: remains the experimental primary architecture.

## Design rule

Do not paste external ISA manuals or Linux source wholesale into ChimeraIIOS. Use clean-room interfaces, generated metadata, SPDX-compatible references, and links to canonical sources. Keep external source trees as separate dependencies or reproducible inputs.
