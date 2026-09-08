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

`include/chimera/unified_isa.hpp` provides a normalized instruction representation for Chimera-8192, RISC-V, AArch64 and x86-64. `include/chimera/isa_catalog.hpp` now adds a compile-time catalog covering representative RISC, CISC and specialized families. `tools/isa/isa_opcodes.csv` and `tools/isa/test_vector_generator.py` provide machine-readable Chimera metadata and deterministic test-vector generation.

External ISA support is extension-based rather than a copied proprietary manual. Canonical specifications should be consulted for implementation details; the repository stores only compatible metadata and original glue code.

## Performance architecture

The project follows proven open-source design patterns:

- QEMU-style translation/backend separation
- LLVM ORC-compatible JIT boundary
- MLIR-style multi-level lowering and dialect conversion
- contiguous limb-based wide arithmetic
- optional x86 assembly hot paths
- capability-based runtime dispatch
- browser GPU rendering separated from native Wayland/EGL
- GPU-side downsampled post-processing for Aurora effects

See `docs/PERFORMANCE_AND_PORTABILITY.md` and `docs/ISA_and_Source_Artifacts.md`.

## Aurora + Unreal Engine 5

An **optional** UE5 Aurora Desktop plugin is now provided under `integrations/ue5/AuroraDesktop/`. It mirrors the Aurora visual model with UMG/Slate and a reusable frosted-glass shader, while Linux builds may connect to Wayland as a client. UE5 remains isolated from the core CMake build.

## Windows kernel integration

`integrations/windows/KMDF_ChmEcho/` contains a safe, isolated KMDF echo sample demonstrating WDF queue setup, buffered IOCTL handling and user-mode testing. It is educational integration code and is not part of the Chimera kernel. See `docs/Windows_Kernel_Dev_and_Snippets.md`.

## Quantum interoperability

`include/chimera/quantum_bridge.hpp` introduces a small provider-neutral circuit IR boundary. It does **not** claim that an ordinary CPU executes quantum states natively. It is designed so a future simulator or QIR-compatible hardware/provider backend can be selected without changing the kernel ISA ABI.

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
/tools/isa      ISA catalog and test-vector tooling
/tests          host-side and QEMU-oriented tests
/integrations   optional UE5 and Windows KMDF adapters
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

GitHub Actions validates the native build on Linux and Windows and publishes the web explorer through GitHub Pages. Native build directories are uploaded as CI artifacts.

## Research and provenance

Do not vendor external manuals or the Linux kernel wholesale. Use canonical links, clean-room interfaces, generated metadata, and compatible licenses. See:

- `docs/ISA_COMPLETE.md`
- `docs/ISA_and_Source_Artifacts.md`
- `docs/LINUX_7X_CROSSWALK.md`
- `docs/SOURCE_LICENSE_BOUNDARIES.md`
- `docs/PERFORMANCE_AND_PORTABILITY.md`
- `docs/MASTER_SOURCE_MAP.md`
- `docs/PROVENANCE.md`
- `docs/W2K-ASM_IMPORT.md`
- `docs/Windows_Kernel_Dev_and_Snippets.md`

The historical `W2K-ASM.txt` material is used only as provenance/reference context; Microsoft Confidential or otherwise restricted source text is not reproduced in the implementation.

## Live demonstrations

- CodeWords technical showcase: https://codewords.agemo.ai/share/html/22980add8f8df4e6c834a970234105a26c98916f152ccff79720c778407fb2ba
- OnHercules live demo: https://chimera-ii-os-730893.onhercules.app/

## License

Repository root is GPL-3.0 unless a file or imported component states otherwise. Third-party and historical source remains subject to its original licensing/provenance requirements.
