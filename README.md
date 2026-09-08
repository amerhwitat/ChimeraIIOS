# Chimera II OS

**Research-grade modular operating-system, virtual-processor, desktop, networking, data, and intelligent-computing ecosystem.**

> Status: research/engineering prototype. Host-emulated components are separated from future bare-metal firmware, kernel, driver, FPGA, and silicon targets.

## Architecture baseline

The repository follows the **Chimera II OS Developer Guide** subsystem order: Spit Fire/Jasper boot, Koronos kernel, RegisterN, Spotnik networking, VFS/TensorFS/Nucleus/Hive data fabric, Aurora graphics, CEF services, security/CI, ISA tooling, and QEMU-oriented tests.

```text
                       CHIMERA II OS
                              |
       +----------------------+----------------------+
       |                      |                      |
  MACHINE PLANE         COGNITIVE PLANE         WORLD PLANE
  R8192 / C8192         128D State             Network / GPU
  RegisterN             Knowledge              Files / Sensors
  Tensor / Vector       Reasoning              Storage / UI
       |                      |                      |
       +----------------------+----------------------+
                              |
                       KORONOS KERNEL
                              |
      ISA / MM / SCHED / IRQ / VFS / IPC / NET
                              |
                   AURORA / GPU / CEF / WEB
```

The 8192-bit processor remains an architectural/emulation research target, not a claim of existing 8192-bit silicon.

## Expandable N-bit runtime

`include/chimera/nbit_runtime.hpp` and `src/runtime/nbit_runtime.cpp` make operand width an explicit runtime property. The same API can represent 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384-bit and future widths subject to capability limits.

Execution modes are capability checked:

- `Scalar` — portable baseline
- `Vector` — SIMD/GPU-oriented backend
- `NativeWide` — RegisterN/WideInt execution
- `JIT` — future LLVM/ORC optimized backend
- `QuantumHybrid` — classical/quantum intermediate-representation boundary

Mode changes fail safely when the selected backend or width is unavailable, preserving backward compatibility.

## ISA integration

`include/chimera/unified_isa.hpp` provides a normalized instruction representation for Chimera-8192, RISC-V, AArch64 and x86-64. External ISA support is extension-based rather than a copied proprietary manual. RISC-V ratified specifications are maintained publicly; QEMU TCG provides a useful reference architecture for multi-ISA translation and emulation.

## Performance architecture

The project now follows several proven open-source design patterns:

- QEMU-style translation/backend separation
- LLVM ORC-compatible JIT boundary
- MLIR-style multi-level lowering and dialect conversion
- contiguous limb-based wide arithmetic
- optional x86 assembly hot paths
- capability-based runtime dispatch
- browser GPU rendering separated from native Wayland/EGL

See `docs/PERFORMANCE_AND_PORTABILITY.md`.

## Quantum interoperability

`include/chimera/quantum_bridge.hpp` introduces a small provider-neutral circuit IR boundary. It does **not** claim that an ordinary CPU executes quantum states natively. It is designed so a future simulator or QIR-compatible hardware/provider backend can be selected without changing the kernel ISA ABI.

QIR is an LLVM-based representation intended to improve interoperability among heterogeneous quantum processors.

## Primary source tree

```text
/boot          Spit Fire / Jasper / x86 bootstrap
/kernel        Koronos + scheduler/MM/IPC/net architecture
/include       stable public kernel, ISA and runtime headers
/src/isa        native and external-ISA decoders
/src/kernel    architecture-neutral kernel skeleton
/src/runtime   N-bit runtime and backend switching
/src/arch       architecture-specific C/ASM fast paths
/net            Spotnik networking
/userspace      Kore / Aurora / CEF / NDB / Hive
/desktop        Aurora Wayland + GPU shaders
/tools          ISA, source provenance and depth-crawl tooling
/tests          host-side and QEMU-oriented tests
/docs           architecture, provenance and research documentation
/web             browser-based ISA/kernel/Aurora explorer
```

## Build and test

```bash
cmake -S . -B build -DCHIMERA_ENABLE_EXPERIMENTAL=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

The optional x86-64 assembly fast path is enabled automatically on supported x86-64 hosts and can be disabled with `-DCHIMERA_ENABLE_X86_ASM=OFF`.

## Web interface and publishing

The static explorer is under `web/`. It can be served locally with:

```bash
python3 -m http.server 8080 --directory web
```

GitHub Actions now validates the native build on Linux and Windows and publishes the web explorer through GitHub Pages. Native build directories are uploaded as CI artifacts.

Cloudflare Pages is also suitable for production edge hosting because it supports GitHub integration, automatic deployments, and preview deployments.

## Research and provenance

Do not vendor external manuals or the Linux kernel wholesale. Use canonical links, clean-room interfaces, generated metadata, and compatible licenses. See:

- `docs/ISA_COMPLETE.md`
- `docs/LINUX_7X_CROSSWALK.md`
- `docs/SOURCE_LICENSE_BOUNDARIES.md`
- `docs/PERFORMANCE_AND_PORTABILITY.md`
- `docs/MASTER_SOURCE_MAP.md`
- `docs/PROVENANCE.md`
- `docs/W2K-ASM_IMPORT.md`

## Live demonstrations

- CodeWords technical showcase: https://codewords.agemo.ai/share/html/22980add8f8df4e6c834a970234105a26c98916f152ccff79720c778407fb2ba
- OnHercules live demo: https://chimera-ii-os-730893.onhercules.app/

## License

Repository root is GPL-3.0 unless a file or imported component states otherwise. Third-party and historical source remains subject to its original licensing/provenance requirements.
