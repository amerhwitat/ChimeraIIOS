# Chimera II Native Toolchain

The native toolchain is source-first and separates **logical N-bit arithmetic** from **physical instruction-set code generation**.

## Languages

- C: `chimera-ncc`
- C++: `chimera-ncc -x=c++`
- Assembly: `chimera-as` and the host LLVM/GNU assemblers
- Linking: LLVM `ld.lld`/GNU `ld` through the selected compiler driver
- Debugging: GDB/LLDB when available

## N-bit model

`--chimera-bits=N` selects the logical integer width. Widths such as 1, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768 and larger are valid as a software representation subject to memory limits.

LLVM's APInt model is the reference design for arbitrary precision compiler integers. The Chimera runtime provides a small freestanding-friendly `uintN` implementation for code that needs a runtime value rather than a compiler constant.

## Physical targets

The architecture registry covers x86/i386/x86-64, ARM/AArch64, RISC-V 32/64, MIPS64, PowerPC64LE, s390x and WebAssembly 32/64, plus the experimental `chimera8192` target contract.

A logical 8192-bit value is **not** claimed to be a native 8192-bit hardware register on commodity CPUs. For real hardware, the compiler emits instructions for the selected physical target and lowers wide arithmetic into multiple machine words. A true Chimera CPU requires a dedicated LLVM/GCC backend and linker/ABI implementation before native Chimera machine code can be claimed.

## Examples

```sh
CHIMERA_BITS=8192 tools/chimera-toolchain/chimera-ncc -std=c17 -O2 -c kernel.c -o kernel.o
CHIMERA_BITS=16384 tools/chimera-toolchain/chimera-ncc -x=c++ -std=c++20 -O2 -c app.cpp -o app.o
```

For a physical cross target, select the appropriate compiler/sysroot or pass the compiler's normal target flags. The architecture registry is intentionally declarative so the build system can discover installed cross compilers rather than assuming every toolchain is present.
