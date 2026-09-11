# Assembler / disassembler integration

ISO-Tool now has a first-class assembler/disassembler registry covering NASM, YASM, GNU binutils, LLVM MC/disassembler, MASM detection and native Chimera II C8192/R8192 adapters.

The pipeline is `dependency scan → backend discovery → target selection → assembly/disassembly → artifact staging → ISO mastering`.

Vendor-restricted tools are detected from installed SDKs instead of redistributed. Open-source components are consumed according to their licenses. Backend paths and versions are recorded for reproducibility.

The native Windows linkage contract explicitly includes `<windows.h>`, `<shlobj.h>` and `#pragma comment(lib, "comctl32.lib")`.
