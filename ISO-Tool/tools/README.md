# ISO-Tool assembler/disassembler toolchain

Chimera II ISO-Tool uses a unified assembler/disassembler registry. Supported and discoverable backends include NASM, YASM, GNU binutils, LLVM MC/LLVM disassembler, Microsoft MASM detection, and native Chimera II C8192/R8192 toolchain hooks.

The registry covers x86/x86-64, ARM/AArch64, RISC-V, MIPS, PowerPC, SPARC and other LLVM/binutils targets when installed. Vendor tools are detected rather than redistributed when their terms do not permit redistribution.

Windows builds use an explicit linkage header containing `<windows.h>`, `<shlobj.h>` and `#pragma comment(lib, "comctl32.lib")`, plus the other Windows libraries required by the native front end.
