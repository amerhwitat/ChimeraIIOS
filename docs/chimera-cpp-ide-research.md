# Chimera II C/C++ IDE and compiler architecture

## Research conclusion

The strongest open-source design references for this integration are Qt Creator, CodeLite and Code::Blocks. Qt Creator is the preferred architectural reference for modern cross-platform tooling because its upstream project supports Windows and Linux and integrates CMake, Ninja, GCC, Clang and Windows CDB workflows. CodeLite is a useful lightweight C/C++-first reference with native Linux and Windows builds. Code::Blocks is a useful reference for a simpler plugin-oriented IDE and its documented support for GCC/MinGW, MSVC, Clang and GDB/CDB.

Sources:
- https://github.com/qt-creator/qt-creator
- https://github.com/eranif/codelite
- https://www.codeblocks.org/features/

## Chimera implementation

Chimera Code should combine these patterns rather than embed a complete upstream IDE wholesale:
- editor, project/workspace and diagnostics model inspired by Qt Creator;
- lightweight compiler configuration and project model inspired by CodeLite;
- straightforward compiler/debugger profiles inspired by Code::Blocks;
- Aurora Web UI integration;
- native adapter boundary for GCC/G++, Clang/Clang++, MSVC/clang-cl and Chimera toolchains;
- GDB/CDB/Chimera debugger adapters;
- CMake/Ninja/Make/Meson integration;
- C/C++ standards through C++23 and compiler-supported C++26 preview features;
- explicit distinction between standardized language versions and compiler extensions.

## Chimera targets

The compiler driver must support host builds plus two target families:
- Chimera CISC: lowers C/C++ IR through a Chimera CISC backend and emits the defined Chimera object/assembly format.
- Chimera RISC: lowers C/C++ IR through a Chimera RISC backend and emits the defined Chimera object/assembly format.

Until complete backend code generation exists, the UI must label these targets as backend-dependent instead of pretending GCC can directly emit Chimera ISA binaries.

## Security and execution boundary

Browser code may edit source and create build plans but must not execute arbitrary host commands. Actual compilation, linking, installation and program execution occur through an authorized local/session adapter with explicit capabilities and workspace restrictions.

## Latest C++ support

C++23 is the production baseline. C++26 is a preview/development target, not a finalized ISO baseline. The `c++26-preview` option is exposed only when the selected compiler advertises support. The IDE must query compiler capabilities rather than assume language or library features are present.

## Aurora registry integration

The approved Aurora registry is schema `chimera-aurora-apps/v7` and exposes `chimera-code` in the Chimera II and Development categories. The web implementation consists of `web/chimera_code_ide.html`, `web/chimera_code_ide.css`, `web/chimera_code_ide.js`, `web/chimera_cpp_toolchain.json` and `web/tests/chimera_cpp_toolchain.test.mjs`.

## Verification

The conformance suite checks the compiler catalog, CISC/RISC target presence, IDE controls and Aurora registry exposure. Runtime compilation remains dependent on the installed host compiler or Chimera backend and an authorized adapter.
