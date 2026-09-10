# Chimera II C++ Toolchain Center

Chimera II provides a unified registry for open-source C++ compilers, IDEs and debuggers. The registry is intentionally curated rather than claiming to contain every project ever published.

## Compilers

- GCC
- LLVM/Clang and clang-cl
- MinGW-w64 GCC toolchain
- TinyCC (kept as an experimental/compatibility entry)
- Open Watcom

## IDEs

- Qt Creator
- Code::Blocks
- KDevelop
- CodeLite
- Eclipse CDT
- Geany

## Debuggers and analysis

- GDB
- LLDB
- rr
- Valgrind

Qt Creator supports GCC/Clang/MinGW and GDB/LLDB through configurable kits; its current documentation also describes compiler and debugger autodetection. LLVM/Clang is integrated as the principal modern alternative compiler family.

## Chimera targets

The toolchain registry exposes x86_64, i686, AArch64, ARM, RISC-V and experimental Chimera C8192/R8192 targets. C8192/R8192 entries are target specifications, not claims that upstream GCC/LLVM already ship those backends.

## ISO policy

The ISO bundles manifests, launchers, source provenance and build recipes. Large third-party IDE/compiler source trees and binary SDKs should be pulled through reproducible package/build jobs instead of silently copying arbitrary upstream binaries into the Git repository. License notices are preserved per component.
