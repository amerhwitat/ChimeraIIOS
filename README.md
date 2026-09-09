# Chimera II OS

**Research-grade modular operating-system, virtual-processor, desktop, networking, data, and intelligent-computing ecosystem.**

> Status: research/engineering prototype. Host-emulated components are separated from future bare-metal firmware, kernel, driver, FPGA, and silicon targets.

## Aurora Wayland Glass Desktop

Aurora is now defined as a **single desktop surface** shared by the native Wayland environment and the browser Web UI. Applications are managed as windows on that surface instead of appearing as an unrelated collection of pages.

The canonical visual reference is the approved **Aurora Wayland Glass Desktop** artwork in the project Library: scenic mountain/lake background, translucent frosted-glass panels, rounded window chrome, blue/purple accents, top bar, left application dock, right widget rail, bottom dock, and glass terminal presentation.

Web desktop contracts:

- `web/aurora_glass_desktop.json`
- `web/aurora_glass_desktop.css`
- `web/aurora_desktop_surface.js`
- `web/aurora_shell.js`
- `web/aurora_apps.json`
- `docs/AURORA_GLASS_DESKTOP_AND_TERMINAL.md`

The production background asset is expected at `web/assets/aurora/aurora-wallpaper.png`. The Library artwork is the visual source of truth; if that binary is absent, the deployment must report that exact-background parity is pending rather than silently claiming pixel identity.

The native stack remains **DRM/KMS → Mesa/Vulkan/OpenGL → Aurora compositor → Wayland clients**, with software rendering fallback. The Web implementation mirrors the surface/window model using managed application windows and constrained embedded pages. External sites remain separate windows.

## Aurora Terminal, commands and `man`

The terminal is a first-class Aurora surface with a dark translucent glass profile:

- JetBrains Mono / Cascadia Code / Fira Code
- `aurora@chimera:~$` prompt
- glass blur and rounded window chrome
- command history, completion, aliases, pipes and redirection
- POSIX/Linux/BSD/System V commands
- Bash/Zsh
- Windows CMD and PowerShell families
- GCC/G++, Clang/Clang++, CMake, Ninja, Make and Meson
- GDB/CDB/Chimera debugger commands
- Chimera ISA assembler/disassembler/runtime commands
- system health, networking, installer, crash and desktop commands

Machine-readable references:

- `web/aurora_terminal_profile.json`
- `web/command_catalog.json`
- `web/man_pages.json`

`man`, `apropos` and `whatis` operate against the unified database. The database contains original concise metadata and does not wholesale vendor copyrighted manuals.

Security/audit commands are restricted to authorized lab/backend adapters.

## Chimera Code IDE and C/C++ toolchain

The Aurora web desktop exposes **Chimera Code IDE** as an approved development application. It provides a Code::Blocks-like focused workflow while following the stronger cross-platform project/toolchain architecture of Qt Creator, with lightweight compiler-profile ideas from CodeLite.

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

Supported language levels include C11/C17/C23 and C++11 through C++23. `c++26-preview` is experimental and compiler-capability-dependent; C++23 is the production baseline.

Chimera targets exposed by the IDE are **Chimera CISC**, **Chimera RISC**, **Chimera Native**, and **Chimera Emulator**. Host GCC/MSVC installations are adapters and do not automatically generate Chimera ISA binaries. CISC/RISC compilation requires the corresponding Chimera frontend/IR/backend/assembler/linker pipeline.

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

The supported workstation path includes the host-side Koronos startup runtime and standard Wayland session integration:

- `src/kernel/chimera_kernel_main.cpp`
- `platform/systemd/chimera-kernel.service`
- `desktop/aurora/aurora-session.sh`
- `platform/wayland/aurora.desktop`
- `platform/systemd/aurora-session@.service`
- `tools/installer/enable-startup.sh`
- `docs/CHIMERA_II_KERNEL_AURORA_STARTUP.md`

Normal workstation flow: **UEFI/BIOS → existing Linux bootloader/kernel → systemd → Koronos runtime → display manager/logind → Aurora Wayland session**.

## Installer and hardware compatibility

The repository includes a safe cross-platform installer planning layer under `tools/installer/`. Disk wiping, partitioning, formatting, bootloader replacement and driver mutation remain privileged adapter operations requiring explicit confirmation.

## Expandable N-bit runtime

`include/chimera/nbit_runtime.hpp` and `src/runtime/nbit_runtime.cpp` make operand width an explicit runtime property. The same API can represent 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384-bit and future widths subject to capability limits.

Execution modes include `Scalar`, `Vector`, `NativeWide`, `JIT` and `QuantumHybrid`, with capability checks and safe failure.

## ISA integration

`include/chimera/unified_isa.hpp` provides a normalized instruction representation for Chimera-8192, RISC-V, AArch64 and x86-64. `include/chimera/isa_catalog.hpp`, `tools/isa/isa_opcodes.csv` and `tools/isa/test_vector_generator.py` provide machine-readable metadata and deterministic test-vector generation.

## Cognitive node and research

`tools/cognition/chimera_rnn.py` provides a dependency-free recurrent-state/provenance prototype. The node network exchanges signed evidence and summaries rather than arbitrary executable code, kernel modules or privileged commands.

## Performance architecture

The project follows proven open-source design patterns including QEMU-style backend separation, LLVM ORC-compatible JIT boundaries, MLIR-style lowering, wide-integer limb arithmetic, optional x86 fast paths, capability dispatch, and browser GPU rendering separated from native Wayland/EGL.

## Primary source tree

```text
/boot /kernel /include /src /net /userspace /desktop /platform
/tools /tests /integrations /docs /web
```

## Build and test

```bash
cmake -S . -B build -DCHIMERA_ENABLE_EXPERIMENTAL=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
python3 tests/installer/test_installer_plan.py
python3 tests/cognition/test_chimera_rnn.py
```

Web explorer:

```bash
python3 -m http.server 8080 --directory web
```

## Live demonstrations

- CodeWords technical showcase
- OnHercules live demo

## License

Repository root is GPL-3.0 unless a file or imported component states otherwise. Third-party and historical source remains subject to its original licensing/provenance requirements.
