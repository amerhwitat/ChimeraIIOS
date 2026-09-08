# Chimera II Performance, Portability and N-bit Expansion

Chimera II treats operand width as a runtime/ABI property rather than baking 8192 bits into every subsystem. Existing 64/128/256-bit code remains valid while the machine plane scales to larger widths.

## Performance strategy

- Normalized instruction representation keeps ISA frontends independent from execution backends.
- `WideInt` uses contiguous 64-bit limbs for portable C++ fallback arithmetic and future architecture-specific acceleration.
- Runtime mode switching is capability-checked: Scalar, Vector, NativeWide, JIT, and QuantumHybrid.
- Optional x86 assembly contains only tiny hot-path primitives; portable C++ remains the semantic baseline.
- The JIT boundary is compatible with LLVM ORC-style lazy/concurrent compilation.
- Multi-level lowering can use MLIR dialect conversion for target-specific lowering.
- QuantumHybrid is a provider-neutral IR boundary, not a claim that classical CPUs become quantum processors.

## N-bit strategy

```text
Application
   |
Chimera IR / ABI
   |
   +-- Scalar -------- host integer types
   +-- Vector -------- SIMD / GPU
   +-- NativeWide ---- RegisterN / WideInt
   +-- JIT ----------- LLVM/ORC-compatible backend
   +-- QuantumHybrid - quantum IR/provider backend
```

A future hardware target can advertise any power-of-two width without changing the kernel API. The ABI should expose width, endianness, alignment, feature bits, and serialization version explicitly.

## Backward compatibility

- Existing `RegisterN<8192>` remains source-compatible.
- New runtime APIs are additive.
- Unsupported widths/modes are rejected instead of silently changing semantics.
- External ISA support remains extension-based; proprietary manuals and whole external kernels are not vendored.

## Host and publishing recommendation

GitHub + GitHub Actions + GitHub Pages provides one reproducible source/CI/web provenance chain. Cloudflare Pages is an optional production edge host with GitHub integration and preview deployments.

Native binaries should be published as CI artifacts/releases. Static/WebAssembly output should be published separately. A browser is never treated as a bare-metal execution environment.

## References

- QEMU TCG: https://www.qemu.org/docs/master/devel/index-tcg.html
- RISC-V: https://docs.riscv.org/
- RISC-V Vector: https://docs.riscv.org/reference/isa/unpriv/v-st-ext
- LLVM ORC JIT: https://llvm.org/docs/ORCv2.html
- MLIR: https://mlir.llvm.org/docs/DialectConversion/
- QIR: https://github.com/qir-alliance/qir-spec
- Cloudflare Pages Git integration: https://developers.cloudflare.com/pages/configuration/git-integration/github-integration/
