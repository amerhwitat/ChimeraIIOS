# Universal CPU Toolchains

Chimera II OS exposes a capability registry for assemblers, disassemblers, compilers, linkers, object utilities, debuggers and CPU emulators.

The open-toolchain baseline is GNU Binutils/GAS/objdump, GCC, LLVM MC/Clang/LLD and QEMU. NASM/YASM are registered for x86 families. Microsoft MASM/MSVC and vendor compiler families are represented as external adapters because their binaries and licenses are not redistributed by Chimera.

A toolchain entry identifies supported CPU targets, tool kinds, detection commands, license class and redistribution policy. Detection is capability discovery: an absent tool is not a build failure unless a selected build profile requires it.

The registry deliberately does not claim that every historical CPU instruction is implemented in Chimera. Native C8192/R8192 execution remains distinct from foreign-ISA translation/emulation/import. Tool output is consumed through the universal ISA and canonical micro-op boundaries.

ISO-Tool stages the registry and provenance metadata; it does not silently package proprietary compiler or assembler binaries.
