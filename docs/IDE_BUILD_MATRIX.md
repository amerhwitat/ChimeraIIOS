# Native IDE / Compiler Build Matrix

| Target | Visual Studio 2022 / MSVC | GNU GCC / Clang | Code::Blocks |
|---|---|---|---|
| ChimeraMachine | `cpp/ChimeraMachine.vcxproj` | root `CMakeLists.txt` | consumed by native project/workspace | 
| ChimeraServer | `cpp/ChimeraServer.vcxproj` | root CMake | `cpp/ChimeraServer.cbp` |
| ChimeraKernel | `cpp/ChimeraKernel.vcxproj` | root CMake on supported POSIX targets | `cpp/ChimeraKernel.cbp` |
| ISO-Tool | `ISO-Tool/vcpp/ISO-Tool-UnifiedGui.sln` | `ISO-Tool/build-gcc.sh` when native engine exists | use GCC-compatible project/toolchain where provided |
| Flash-Tool | `Flash-Tool/ChimeraFlashTool.sln` | `Flash-Tool/build.sh` | `Flash-Tool/ChimeraFlashTool.cbp` |

## Recommended order

1. Install the compiler/IDE and CMake.
2. Run the dependency probe/build orchestrator.
3. Configure/build the native OS.
4. Build ISO-Tool.
5. Build Flash-Tool.
6. Run unit/conformance tests.
7. Inspect generated artifacts before any image deployment.

Visual Studio can consume CMake directly and can also generate/use MSBuild project files. Code::Blocks uses `.cbp` project files and delegates compilation/linking to the configured external compiler. citeturn0search0turn0search1

## Important distinction

The `.sln`/`.vcxproj` and `.cbp` files are deterministic IDE entry points. The root CMake build remains the cross-platform source of truth. A checked-in project file does not by itself prove that every platform-specific target compiles; native CI is the verification authority.
