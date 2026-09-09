# Chimera II OS

**Research-grade modular operating-system, virtual-processor, desktop, networking, data, and intelligent-computing ecosystem.**

> Status: research/engineering prototype. Host-emulated components are separated from future bare-metal firmware, kernel, driver, FPGA, and silicon targets.

## Chimera Code IDE and C/C++ toolchain

The Aurora web desktop now exposes **Chimera Code IDE** as an approved development application. It provides a Code::Blocks-like focused workflow while following the stronger cross-platform project/toolchain architecture of Qt Creator, with lightweight compiler-profile ideas from CodeLite.

Supported host toolchains:

- GCC / G++
- Clang / Clang++
- MSVC
- Clang-cl

Supported build systems:

- CMake
- Ninja
- Make
- Meson

Supported debugger adapters:

- GDB
- CDB / WinDbg-compatible Windows workflow
- Chimera debugger

Supported language levels include C11/C17/C23 and C++11 through C++23. `c++26-preview` is exposed only as an experimental, compiler-capability-dependent mode; C++23 is the production baseline.

Chimera targets exposed by the IDE are **Chimera CISC**, **Chimera RISC**, **Chimera Native**, and **Chimera Emulator**. Host GCC/MSVC installations are adapters and do not automatically generate Chimera ISA binaries. CISC/RISC compilation requires the corresponding Chimera frontend/IR/backend/assembler/linker pipeline.

The web frontend does not execute arbitrary host commands. Build, run, debug and installation operations cross an explicit authorized local/session adapter boundary with capability and workspace restrictions.

Relevant files:

- `web/chimera_code_ide.html`
- `web/chimera_code_ide.css`
- `web/chimera_code_ide.js`
- `web/chimera_cpp_toolchain.json`
- `web/tests/chimera_cpp_toolchain.test.mjs`
- `docs/chimera-cpp-ide-research.md`

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

## Kernel startup and Aurora boot

The current supported workstation path now includes a **host-side Koronos startup runtime** and standard Wayland session integration:

- `src/kernel/chimera_kernel_main.cpp` — starts the architecture-neutral Koronos kernel runtime and publishes `/run/chimera/kernel.ready`.
- `platform/systemd/chimera-kernel.service` — starts the kernel runtime during normal Linux boot.
- `desktop/aurora/aurora-session.sh` — launches a native `aurora-compositor` when available, otherwise a supported Wayland compatibility compositor.
- `platform/wayland/aurora.desktop` — exposes Aurora to standard display managers.
- `platform/systemd/aurora-session@.service` — optional advanced system-service launch for embedded/lab deployments.
- `tools/installer/enable-startup.sh` — enables the kernel startup service safely.
- `docs/CHIMERA_II_KERNEL_AURORA_STARTUP.md` — complete startup and failure model.

The normal workstation flow is **UEFI/BIOS → existing Linux bootloader/kernel → systemd → Koronos runtime → display manager/logind → Aurora Wayland session**. The present Koronos runtime is not represented as a freestanding Linux-replacement kernel; a future bare-metal boot image remains a separate implementation stage.

## Installer and hardware compatibility

The repository includes a **safe, cross-platform installer planning layer** under `tools/installer/`. It is Linux/Unix-oriented but includes Windows Server/workstation planning and driver-catalog compatibility.

- `tools/installer/installer_plan.py` — hardware/driver/network/storage installation plan.
- `tools/installer/installer_capabilities.json` — machine-readable compatibility matrix.
- `tools/installer/chimera-installer.sh` — Linux entrypoint.
- `tools/installer/ChimeraInstaller.ps1` — Windows entrypoint.
- `docs/CHIMERA_II_INSTALLER_AND_HARDWARE_COMPATIBILITY.md` — step-by-step installer architecture.
- `docs/CHIMERA_II_FILESYSTEM_LAYOUT.md` — ten-level Chimera filesystem reference.
- `docs/CHIMERA_II_STANDARDS_BASELINE.md` — UEFI/ACPI/PCI/USB/NVMe/GPT/storage/graphics/network standards baseline.
- `docs/CHIMERA_II_SOURCE_CATALOG.md` — bounded authoritative-source and link traversal catalog.

The planner is **non-destructive by default**. Disk wiping, partitioning, formatting, bootloader replacement and driver mutation remain privileged adapter operations requiring explicit confirmation.

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

## Aurora desktop

Aurora is the Chimera Wayland-first desktop target. Its intended stack is DRM/KMS → Mesa/Vulkan/OpenGL → Aurora compositor → Wayland clients, with software-rendering fallback. The installer can enable Aurora for workstation/developer profiles or leave it disabled for servers.

## Cognitive node and RNN/SSM research

`tools/cognition/chimera_rnn.py` provides a dependency-free recurrent-state/provenance prototype. `docs/CHIMERA_II_COGNITIVE_NETWORK.md` defines an opt-in mTLS/allowlist knowledge-node architecture. `docs/CHIMERA_II_COMPUTATIONAL_RESEARCH_BASELINE.md` tracks RNN, state-space, neuro-symbolic and graph-learning research directions.

The node network exchanges signed evidence and summaries—not arbitrary executable code, kernel modules or privileged commands—and does not perform unrestricted Internet scanning.

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

An **optional** UE5 Aurora Desktop plugin is provided under `integrations/ue5/AuroraDesktop/`. It mirrors the Aurora visual model with UMG/Slate and a reusable frosted-glass shader, while Linux builds may connect to Wayland as a client. UE5 remains isolated from the core CMake build.

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
/src/kernel    architecture-neutral kernel skeleton + startup runtime
/src/runtime   N-bit runtime and backend switching
/src/arch       architecture-specific C/ASM fast paths
/net            Spotnik networking
/userspace      Kore / Aurora / CEF / NDB / Hive
/desktop        Aurora Wayland + GPU shaders
/platform       systemd + Wayland session integration
/tools/isa      ISA catalog and test-vector tooling
/tools/installer installer planning and compatibility
/tools/cognition temporal state and evidence prototype
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
python3 tests/installer/test_installer_plan.py
python3 tests/cognition/test_chimera_rnn.py
```

The optional x86-64 assembly fast path is enabled automatically on supported x86-64 hosts and can be disabled with `-DCHIMERA_ENABLE_X86_ASM=OFF`.

## Web interface and publishing

The static explorer is under `web/`. It can be served locally with:

```bash
python3 -m http.server 8080 --directory web
```

GitHub Actions validates the native build and publishes the web explorer when configured. Public-repository GitHub Actions runners are available without charge under GitHub's public-repository policy.

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
- `docs/CHIMERA_II_INSTALLER_AND_HARDWARE_COMPATIBILITY.md`
- `docs/CHIMERA_II_STANDARDS_BASELINE.md`
- `docs/CHIMERA_II_COGNITIVE_NETWORK.md`
- `docs/CHIMERA_II_KERNEL_AURORA_STARTUP.md`

The historical `W2K-ASM.txt` material is used only as provenance/reference context; Microsoft Confidential or otherwise restricted source text is not reproduced in the implementation.

## Live demonstrations

- CodeWords technical showcase: https://codewords.agemo.ai/share/html/22980add8f8df4e6c834a970234105a26c98916f152ccff79720c778407fb2ba
- OnHercules live demo: https://chimera-ii-os-730893.onhercules.app/

## License

Repository root is GPL-3.0 unless a file or imported component states otherwise. Third-party and historical source remains subject to its original licensing/provenance requirements.
