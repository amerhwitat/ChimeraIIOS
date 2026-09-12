# Build Automation

Chimera II OS is now **native-first** for its kernel, ISA, platform and build metadata paths.

## Primary native entry points

### Windows / Visual Studio / MSVC

```bat
cpp\build-msvc.bat Release x64
build-native-all.bat Release
```

`cpp/ChimeraIIOS.sln` provides the native IDE solution. x64 MASM fast paths are compiled from `asm/x86_64/chimera_fastpath.asm` when the MSVC toolchain supports MASM.

### GNU/Linux and POSIX

```bash
./cpp/build-gcc.sh Release
./build-native-all.sh Release
```

CMake selects the architecture assembly implementation for x86-64, AArch64 and RISC-V64.

### Code::Blocks

Use the `.cbp` projects under `cpp/` for the native C++ targets and configure Code::Blocks to use GCC/MinGW or another supported compiler.

## Native replacement policy

Python utilities that participate in the core build/metadata path are being replaced by compiled C++ equivalents rather than copied line-for-line. Current native tools include:

- `chimera_native_tools`: toolchain + memory/ISA metadata validation.
- `chimera_isa_generator`: native CSV-to-JSON ISA metadata generation.

The original Python utilities remain available as reference/research tools where useful. They are not a runtime dependency of the native validation target.

## Language boundaries

- **ASM:** CPU-specific instructions, barriers and hot paths.
- **C:** freestanding and ABI-oriented kernel primitives.
- **C++:** kernel services, ISA, machine model, native tools and host integration.
- **Python:** optional research, ML, data preparation and compatibility/reference tooling.

## Full pipeline

```bat
build-native-all.bat Release
```

or:

```bash
./build-native-all.sh Release
```

The pipeline builds the native OS, executes native metadata validation, builds ISO-Tool, and builds the mobile Flash-Tool. A successful build command is not treated as a claim of hardware boot success; target hardware/emulator validation remains a separate stage.
