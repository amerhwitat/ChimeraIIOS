# Chimera II Native Multi-Language Toolchain

The Chimera toolchain separates **logical N-bit arithmetic** from **physical ISA code generation**. The common integration layer is LLVM IR/MLIR where available, with native language frontends and explicit C ABI boundaries.

## Languages

| Language | Driver | Native integration |
|---|---|---|
| C | `chimera-ncc` | Clang/GCC + Chimera SDK |
| C++ | `chimera-ncc -x=c++` | Clang/LLVM + Chimera SDK |
| Assembly | `chimera-as` | CHIMERA-BIT / target assembler |
| Rust | `chimera-rustc` | rustc/Cargo + C ABI |
| Python | `chimera-python` | CPython + native extension SDK |
| Java | `chimera-javac` | javac/JVM + JNI/FFM bridge |
| Zig | `chimera-zig` | zig when installed |
| Go | `chimera-go` | Go toolchain when installed |
| Fortran | `chimera-fortran` | gfortran when installed |
| Swift | `chimera-swift` | swiftc when installed |

The drivers deliberately use installed upstream compilers rather than vendoring third-party compiler sources into the OS image.

## Common SDK libraries

The native SDK exposes the shared Chimera ABI to all supported languages:

- `chimera_kernel`
- `chimera_fs`
- `chimera_net`
- `chimera_graphics`
- `chimera_tensor`
- `chimera_runtime`
- `chimera_nbit`
- `chimera_ffi`

The existing C/C++ SDK model in the project is retained and is now complemented by Rust, Python and Java bindings. The Python layer is designed around CPython's Limited/Stable ABI (`abi3`/`abi3t`) where appropriate. Java uses JNI and the modern Foreign Function & Memory API instead of requiring generated native glue for every call.

## Intermediate representation

Preferred compilation path:

```text
Python / Java / Rust / C / C++ / Zig / Go / Fortran / Swift / ASM
                              |
                    frontend / binding layer
                              |
                       LLVM IR / MLIR
                              |
                     Chimera optimization
                              |
                 +------------+-------------+
                 |                          |
        physical target             Chimera backend
 x86/AArch64/RISC-V/etc.        R8192/C8192 research ISA
```

MLIR is used as the extensible multi-level representation where it provides value for tensor, accelerator, dataflow and domain-specific transformations; LLVM remains the lower-level optimizer/code generator. This follows the upstream division of responsibilities rather than duplicating LLVM's register allocation/code generation in Chimera userland.

## N-bit model

`--chimera-bits=N` selects the logical integer width. Widths such as 1 through 8192, 16384, 32768 and larger are software representations subject to memory limits.

A logical 8192-bit value is **not** claimed to be a native 8192-bit hardware register on commodity CPUs. Real hardware targets lower it into their physical word/vector instructions. A true Chimera CPU requires a dedicated backend, ABI and linker implementation before native Chimera machine code can be claimed.

## Examples

```sh
CHIMERA_BITS=8192 tools/chimera-toolchain/chimera-ncc -std=c17 -O2 -c kernel.c -o kernel.o
CHIMERA_BITS=16384 tools/chimera-toolchain/chimera-ncc -x=c++ -std=c++20 -O2 -c app.cpp -o app.o
CHIMERA_BITS=8192 tools/chimera-toolchain/chimera-rustc --crate-type lib src/lib.rs
CHIMERA_BITS=8192 tools/chimera-toolchain/chimera-python -c 'import chimera; print(chimera.LOGICAL_BITS)'
tools/chimera-toolchain/chimera-javac Main.java
```

See `languages.json` for the machine-readable language, target and library registry.
