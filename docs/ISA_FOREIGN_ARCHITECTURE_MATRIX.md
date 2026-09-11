# Foreign ISA Coverage Matrix

This matrix records architectures that Chimera II can target through an adapter, decoder, emulator, or compiler backend. It does not claim that every foreign instruction has been assigned a native Chimera opcode.

| Architecture | Coverage target | Integration mode |
|---|---|---|
| x86/x86-64 | Core integer, SIMD, system and virtualization semantics | Decoder/emulator/backend adapter |
| AArch32/AArch64 | ARM/Thumb/AArch64 and system instructions | Decoder/emulator/backend adapter |
| RISC-V32/64 | Base ISA plus ratified extensions | Decoder/emulator/backend adapter |
| MIPS32/64 | Integer, FPU, SIMD/legacy system semantics | Decoder/emulator/backend adapter |
| PowerPC/POWER64 | Integer, vector, system and ABI semantics | Decoder/emulator/backend adapter |
| SPARC | Integer, privileged and ABI semantics | Decoder/emulator/backend adapter |
| SystemZ/s390x | Integer, decimal, vector and ABI semantics | Decoder/emulator/backend adapter |
| 68k | Classic integer, addressing and supervisor semantics | Emulator/compatibility adapter |
| Alpha | Integer, memory ordering and PAL abstractions | Emulator/compatibility adapter |
| PA-RISC | Integer, memory and system semantics | Emulator/compatibility adapter |
| SuperH | SH integer/control semantics | Emulator/compatibility adapter |
| Itanium | EPIC instruction bundles and ABI | Emulator/translation adapter |
| AVR | 8-bit MCU instructions and peripherals | Emulator/embedded adapter |
| Xtensa | Configurable embedded ISA profiles | Emulator/backend adapter |
| WebAssembly | Wasm virtual ISA | Runtime/JIT adapter |
| AMDGPU | GPU instruction families | GPU backend adapter |
| NVPTX | GPU virtual ISA | GPU backend adapter |

LLVM documents a broad target architecture set and a retargetable backend model; its current documentation includes x86, ARM/AArch64, RISC-V, PowerPC, SystemZ, MIPS and GPU targets. Chimera uses that model as an integration reference rather than copying LLVM wholesale.

## Rule for the canonical ISA

Foreign instructions map to canonical Chimera micro-operations when semantics can be represented safely. Architecture-specific behavior that cannot be represented without loss remains in the foreign adapter. Native R8192/C8192 opcodes are reserved for explicitly defined Chimera semantics.

## Mobile

The Mobile Microkernel uses AArch64 as the primary native host and RISC-V64 as a secondary port. Foreign architectures are emulator/translation targets and are never required in the privileged mobile core.
