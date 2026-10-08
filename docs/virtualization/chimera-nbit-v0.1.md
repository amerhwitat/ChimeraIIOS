# Chimera N-bit experimental ISA v0.1

Status: **reference interpreter prototype only**. This is a new, non-ratified experimental ISA; it is not compatible with RISC-V, x86, or another established ISA. Do not use it for security boundaries or production workloads.

## Architectural parameters

- Configurable GPR width N: 32, 64, or 128 bits.
- Sixteen integer registers r0-r15; r0 is hardwired to zero.
- Fixed 32-bit instruction words, little-endian fetch, 4-byte instruction alignment.
- 12-bit signed immediate; arithmetic results wrap modulo 2^N.
- Flat byte-addressed RAM, default 64 KiB, bounds-checked; load/store width is N/8.
- Initial privilege model: single execution mode only. No MMU, page tables, PMP, atomics, interrupt controller, or user/kernel isolation in v0.1.
- Trap vector defaults to address 0x100; illegal instruction, instruction misalignment, load/store bounds faults and software trap are reported by the reference interpreter. Faults are recorded, but full architectural trap-frame/return semantics are not yet specified.
- Initial device model is a deterministic event log for software traps. Console, timer, block, and interrupt-controller devices are planned but not implemented.

## Encoding

Instruction word layout:

| Bits | Field |
|---|---|
| 31:24 | opcode |
| 23:20 | rd |
| 19:16 | ra |
| 15:12 | rb |
| 11:0 | signed immediate |

Initial opcode table:

| Opcode | Mnemonic | Semantics |
|---:|---|---|
| 0x00 | NOP | no operation |
| 0x01 | LI | rd = sign-extended immediate modulo 2^N |
| 0x02 | ADD | rd = ra + rb modulo 2^N |
| 0x03 | SUB | rd = ra - rb modulo 2^N |
| 0x04 | AND | bitwise AND |
| 0x05 | OR | bitwise OR |
| 0x06 | XOR | bitwise XOR |
| 0x10 | LOAD | load N/8 bytes from ra + immediate |
| 0x11 | STORE | store rb to ra + immediate |
| 0x20 | JMP | relative branch in instruction words |
| 0x21 | JZ | branch if ra equals zero |
| 0x30 | TRAP | software trap/event |
| 0xff | HALT | stop interpreter |

## ABI and boot status

v0.1 has no finalized firmware, executable file format, calling convention, system-call ABI, device-tree format, or boot protocol. The machine profile is a design placeholder and remains disabled in the hypervisor backend registry. A production QEMU target must not be enabled until those interfaces and device semantics are specified and tested.

## Tests and coverage

Reference tests cover arithmetic, wraparound, zero register, load/store, branch, illegal opcode, memory bounds, width validation, and step budget. They are unit tests, not official conformance tests. Coverage status: documented prototype = yes; encoded/decoded/executed in reference interpreter = partial; bootable guest = no; architectural conformance suite = not available/not run.

## Planned v0.2

Define precise exception vectors and trap return, instruction privilege policy, memory-map and MMIO bus, timer/interrupt semantics, image format and ABI, then build a tiny ROM/guest test fixture before considering a QEMU system target.
