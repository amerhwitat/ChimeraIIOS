# Chimera II ISA Integration

## Scope

Chimera II now exposes the supplied **Chimera-R8192 native ISA** as a first-class fetch/decode/execute contract, while retaining interoperability-oriented decoders for RV32I/RV64I, AArch64 and x86-64. The native specification occupies opcodes `0x0001..0x011C` (284 instructions).

The canonical machine-readable native registry is `tools/isa/chimera_r8192_opcode_index.csv`. The implementation name/dispatch table is embedded in `src/isa/chimera_isa.cpp`, and the public interface is `include/chimera/isa8192.hpp`.

## Fetch phase

1. Fetch reads the first 16 bits as a **little-endian 16-bit Chimera opcode**.
2. The next three 16-bit fields are decoded as `rd`, `srcA`, and `srcB`.
3. Immediate-bearing instructions may extend the packet to 16 bytes with a 64-bit little-endian immediate.
4. The fetch/decode layer recognizes every supplied opcode from `0x0001` through `0x011C`.
5. Undefined opcodes are rejected before execution.

This replaces the previous 8-bit native-opcode assumption and preserves the existing CPU8192 register model of 1024 × 8192-bit registers.

## Execute phase

The execution dispatcher now has four explicit outcomes:

- `Executed` — native semantics completed.
- `PrivilegeViolation` — a privileged instruction was requested from user mode.
- `InvalidOpcode` — the opcode is outside the supplied native ISA.
- `UnimplementedService` — the opcode is valid and recognized, but requires an OS/device backend that is not yet bound into the emulator.

Native execution currently covers the core R8192 ALU/compare path: `ADD`, `SUB`, `AND`, `OR`, `XOR`, `NOT`, `SHL`, `SHR`, `ROL`, `ROR`, `MUL`, `MULHI`, `DIV`, `REM`, `CMP`, `CMPEQ`, `CMPLT`, and `MOV`. `TRAP`, `SYS_CALL`, `SVC`, `FENCE`, and `BARRIER` are recognized control/system operations. The remaining DMA, networking, VFS, NDB/HIVE, Aurora/GPU, PCI, security, scheduling and service operations are intentionally represented as dispatchable ISA services until their corresponding backend is attached.

## Document phase

The supplied ISA schema is preserved as:

`mnemonic;opcode;encoding;operands;privilege;latency;throughput;pipeline_stage;isa_family;notes;source_ref`

The ISA is partitioned conceptually into:

- `0x0001..0x001A` — R8192 arithmetic, logic, shifts, multiply/divide and memory primitives.
- `0x001B..0x002B` — page pinning, DMA, IOMMU and Spotnik zero-copy networking.
- `0x002C..0x0048` — system, audit, TPM, crypto, module and trap/syscall operations.
- `0x0049..0x0068` — interrupt, cache, tracing, scheduling, locking and memory-management operations.
- `0x0069..0x006F` — frame/DMA/network service operations.
- `0x0070..0x0084` — VFS/file-system operations.
- `0x0085..0x008B` — NDB and HIVE data services.
- `0x008C..0x00B4` — Aurora GPU, media, framebuffer and Wayland presentation operations.
- `0x00B5..0x00C5` — VirtIO, PCI and persistent-memory operations.
- `0x00C6..0x00E6` — kernel lifecycle, PMU, tracing, synchronization, paging and SMP operations.
- `0x00E7..0x0106` — power/thermal, certificate/keystore, licensing, backup, quota, authentication and policy services.
- `0x0107..0x011C` — configuration, cluster/service management, diagnostics, maintenance and security scanning.

## Pipeline contract

The supplied `pipeline_stage`, `latency`, and `throughput` fields are retained as architectural metadata. They are descriptive scheduling targets for the research processor model, not measurements of a fabricated physical implementation. The executor must not infer real hardware timing solely from these fields.

## Validation

`tests/unit/test_r8192_isa.cpp` verifies:

- 16-bit opcode fetch and operand extraction.
- Recognition of the complete 284-opcode range.
- Metadata lookup for `SHA256`.
- Privilege enforcement for `POLICY_UPDATE`.

## External ISA policy

RISC-V is an open standard with a small base ISA plus optional extensions. See https://docs.riscv.org/ and https://github.com/riscv/riscv-isa-manual .

x86-64 is a CISC ISA. Intel publishes the architecture and instruction references in its Software Developer Manuals. See https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html .

AArch64 is included as a compatibility target; Arm publishes architecture documentation for its instruction descriptions.

Do not paste external ISA manuals or Linux source wholesale into ChimeraIIOS. Use clean-room interfaces, generated metadata, SPDX-compatible references, and links to canonical sources.
