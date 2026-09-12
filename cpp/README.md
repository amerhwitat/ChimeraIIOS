# Chimera II OS — Native ASM/C/C++ Build Layer

This directory is the primary native build surface for Chimera II OS. It keeps Visual Studio, GNU/GCC, Clang, Code::Blocks and CMake metadata separate from Python, Java, Node.js, .NET and other language implementations.

## Start here

### Visual Studio 2022 / MSVC

From a Developer Command Prompt:

```bat
cpp\build-msvc.bat Release x64
```

Or open `cpp\ChimeraIIOS.sln` in Visual Studio 2022 and build `Release|x64`.

The x64 MSVC path uses MASM for `asm/x86_64/chimera_fastpath.asm` where supported.

### GNU GCC / Clang / Code::Blocks

```bash
./cpp/build-gcc.sh Release
```

The canonical cross-platform build remains:

```bash
cmake -S . -B build/gcc -DCMAKE_BUILD_TYPE=Release
cmake --build build/gcc --parallel
ctest --test-dir build/gcc --output-on-failure
```

CMake selects architecture assembly for x86-64, AArch64 or RISC-V64. Code::Blocks projects use the configured external GCC/MinGW or other compiler.

## Native targets

- `ChimeraMachine` — ISA, kernel services, memory bus, networking, neural/trust and database backend native code.
- `ChimeraServer` — host server executable.
- `ChimeraKernel` — host-side kernel startup runtime where supported.
- `chimera_native_tools` — compiled metadata/toolchain/memory validation.
- `chimera_isa_generator` — compiled ISA metadata generator.
- ISO-Tool — native C++ implementation under `ISO-Tool/`.
- Flash-Tool — native mobile image validation frontend under `Flash-Tool/`.

## Repository layout

```text
asm/
  x86_64/chimera_fastpath.asm       # MSVC/MASM
  aarch64/chimera_fastpath.S        # GNU/Clang
  riscv64/chimera_fastpath.S        # GNU/Clang

cpp/
  CMakeLists.txt
  ChimeraIIOS.sln
  ChimeraMachine.vcxproj
  ChimeraServer.vcxproj
  ChimeraKernel.vcxproj
  ChimeraServer.cbp
  ChimeraKernel.cbp
  ChimeraIIOS.workspace
  build-msvc.bat
  build-msvc.ps1
  build-gcc.sh
  build-codeblocks.bat

src/
  chimera.c                         # C core/ABI layer
  isa/ kernel/ memory/ net/ ...     # C++ native subsystems
  tools/                             # native replacements for core Python utilities
```

## Python conversion boundary

Core build and metadata validation no longer depends on Python. Native C++ equivalents are under `src/tools/`. Python scripts remain as reference/research implementations where translation would add no runtime value, particularly ML/data-processing utilities.

Generated binaries and intermediate files belong in `build/`, `out/`, `bin/` or CI artifacts and should not be committed.
