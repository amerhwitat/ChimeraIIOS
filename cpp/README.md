# Chimera II OS — Native C/C++ Build Layer

This directory is the native C/C++ build surface for Chimera II OS. It keeps Visual Studio, GNU/GCC, Clang, Code::Blocks and CMake build metadata separate from Python, Java, Node.js, .NET and other language implementations.

## Start here

### Visual Studio 2022 / MSVC

From a Developer Command Prompt:

```bat
cpp\build-msvc.bat Release x64
```

Or open `cpp\ChimeraIIOS.sln` in Visual Studio 2022 and build `Release|x64`.

Visual Studio has first-class CMake support, but the checked-in `.sln`/`.vcxproj` files provide a deterministic Windows/MSBuild entry point for the native targets. Microsoft recommends MSBuild for Windows-specific projects and CMake for cross-platform C++ projects. citeturn0search7turn0search0

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

Code::Blocks project files are under this directory. Code::Blocks uses `.cbp` project files and delegates compilation/linking to an external compiler such as GCC/MinGW or another configured toolchain. citeturn0search1

## Native targets

- `ChimeraMachine` — static library containing ISA, kernel services, memory bus, networking, neural/trust and database backend native code.
- `ChimeraServer` — host server executable.
- `ChimeraKernel` — host-side kernel startup runtime where the selected platform supports it.
- ISO-Tool — native C++ implementation under `ISO-Tool/vcpp`.
- Flash-Tool — mobile image validation/packaging/flash-command frontend under `Flash-Tool`.

## Repository layout

```text
cpp/
  README.md
  CMakeLists.txt
  ChimeraIIOS.sln
  ChimeraMachine.vcxproj
  ChimeraServer.vcxproj
  ChimeraKernel.vcxproj
  ChimeraMachine.cbp
  ChimeraServer.cbp
  ChimeraKernel.cbp
  ChimeraIIOS.workspace
  build-msvc.bat
  build-msvc.ps1
  build-gcc.sh
  build-codeblocks.bat
  run-chimera.bat
  run-chimera.sh
```

Generated files belong in `build/`, `out/`, `bin/` or CI artifacts and should not be committed.
