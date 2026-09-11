# Assembler / disassembler integration

ISO-Tool uses a first-class universal CPU toolchain capability registry covering GNU Binutils/GAS/objdump, LLVM MC/llvm-objdump, NASM, YASM, MASM/MSVC detection, GCC/Clang compiler backends, QEMU emulation and external vendor adapters. The authoritative capability catalog is `../toolchains/registry.json`.

The pipeline is `dependency scan -> backend discovery -> target selection -> assembly/disassembly -> universal-ISA lowering -> artifact staging -> ISO mastering`.

Vendor-restricted tools are detected from installed SDKs instead of redistributed. Open-source components are consumed according to their licenses. Backend paths and versions are recorded for reproducibility.

The native Windows linkage contract explicitly includes `<windows.h>`, `<shlobj.h>` and `#pragma comment(lib, "comctl32.lib")`.

Assembler/disassembler availability never implies that a foreign ISA is native Chimera execution. Decoded instructions cross the canonical semantic micro-op boundary before translation, emulation or native execution.
