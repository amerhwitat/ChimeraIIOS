# Native toolchain and Aurora IDE integration

## What is wired up
- The browser IDE associates common .c, .h, .cc, .cpp, .cxx, .hpp, .asm, .s, .S, .json, and .txt files with editor modes.
- Open Source reads a user-selected local file. Save Source downloads the current buffer under its source filename. This is browser-local file handling, not unrestricted filesystem access.
- Build/Run/Debug send an explicit request to /api/chimera/toolchain. When no configured adapter is available, the UI reports the failure instead of pretending a build ran.
- web/aurora-ide-catalog.json links to official IDE download pages. The OS package manager should verify signatures/checksums and honor each package's license. The browser UI does not install applications silently.

## Native compiler/linker truth
tools/toolchain/chimera-cc, chimera-cxx, and chimera-ld are drivers for installed GCC/Clang and GNU/LLVM linkers. Those compile supported host/cross targets when a suitable compiler, target backend, sysroot and runtime are installed. They do not by themselves implement a production C/C++ backend for the experimental NCB1 ISA. The existing C++ chimera-as currently emits a 16-byte fixed record stream; that stream is not yet a complete relocation-capable NCB1 object ABI.

## Next requirements for production
1. Freeze the NCB1 object ABI, symbols, relocation types, debug format and calling convention.
2. Implement real parser/lexer, two-pass labels, section directives, relocation-aware assembler and inverse disassembler.
3. Add LLVM/GCC backend or a verified C/C++ frontend-to-NCB1 compiler and runtime libraries.
4. Implement linker symbol resolution, section placement, relocations, imports and loader validation.
5. Connect the IDE adapter to an authenticated, sandboxed local toolchain service. Never execute uploaded source in the browser.
