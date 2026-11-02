# Universal CPU Toolchains

Chimera II OS exposes a capability registry for assemblers, disassemblers, compilers, linkers, object utilities, debuggers and CPU emulators.

The open-toolchain baseline is GNU Binutils/GAS/objdump, GCC, LLVM MC/Clang/LLD and QEMU. NASM/YASM are registered for x86 families. Microsoft MASM/MSVC and vendor compiler families are represented as external adapters because their binaries and licenses are not redistributed by Chimera.

A toolchain entry identifies supported CPU targets, tool kinds, detection commands, license class and redistribution policy. Detection is capability discovery: an absent tool is not a build failure unless a selected build profile requires it.

The registry deliberately does not claim that every historical CPU instruction is implemented in Chimera. Native C8192/R8192 execution remains distinct from foreign-ISA translation/emulation/import. Tool output is consumed through the universal ISA and canonical micro-op boundaries.

ISO-Tool stages the registry and provenance metadata; it does not silently package proprietary compiler or assembler binaries.

## Native compiler/linker implementation

Chimera II OS now ships an integration layer for the native open toolchain:

- `chimera-cc`: C compiler driver using GCC by default or Clang with `CHIMERA_NATIVE_COMPILER=clang`.
- `chimera-cxx`: C++ compiler driver using G++ by default or Clang++.
- `chimera-gas`: GNU as/LLVM MC/NASM selection through `CHIMERA_ASSEMBLER`.
- `chimera-ld`: GNU BFD ld or LLVM LLD selection through `CHIMERA_NATIVE_LINKER`.
- `chimera-as`: the existing Chimera ISA assembler, intentionally kept separate from GNU as.

The drivers do not replace GCC, LLVM, Binutils or NASM. They establish a stable Chimera SDK command contract and preserve the upstream licensing of each underlying component. GCC documents the normal C/C++ compilation pipeline and Binutils supplies the assembler/linker/object-tool layer; Clang documents the same compiler-to-assembler/linker pipeline and LLD is available as an LLVM linker. citeturn0search0turn0search2turn1search12

Native mode produces host-native executables. Cross compilation is selected explicitly with a target compiler/sysroot; it is not a claim that physical x86-64, AArch64 or RISC-V processors contain Chimera's virtual RegisterN-wide registers.


## Expanded language and HDL provider coverage

The shared catalog now includes 66 language/runtime families, including V, Odin, experimental Carbon, MATLAB/Octave, Wolfram Language, SAS, Raku, Elm, Haxe, ReScript, Solidity, Vyper, Move, Verilog, SystemVerilog and VHDL. It separately inventories 13 assemblers and 11 disassembly/reverse-engineering providers, including LLVM ML, external ARM/IAR assemblers, MSVC dumpbin and Apple Mach-O inspection tools.

ChimeraIIOS and OctavianOS consume the same `CHM-LANGUAGE-TOOLCHAIN-1` contract. Octavian's canonical copy is under `vendor/chimera-ii-os/source/`. The catalog describes discoverable providers and install profiles; it does not imply that every optional compiler, commercial license, runtime, SDK, CPU backend or sysroot is included in the ISO. Proprietary MATLAB, Wolfram, SAS, MASM, ARM Compiler, IAR and Apple tooling remains externally installed. Carbon is explicitly experimental. Verilog/SystemVerilog/VHDL tools are hardware-description-language tools, not general-purpose CPU compilers.

The optional `hardware-description` profile adds Icarus Verilog, Verilator, GHDL and Yosys package mappings. Installation remains explicit and package-manager-dependent. The profile installer validates the package plan but does not turn provider metadata into proof of successful compilation; CI must run provider-specific smoke tests on hosts where the tools are installed.
