# Chimera II OS

**Research-grade modular operating-system, virtual-processor, desktop, networking, data, and intelligent-computing ecosystem.**

> Status: research/engineering prototype. Host-emulated components are separated from future bare-metal firmware, kernel, driver, FPGA, and silicon targets.

## Architecture baseline

The repository follows the **Chimera II OS Developer Guide** subsystem order: Spit Fire/Jasper boot, Koronos kernel, RegisterN, Spotnik networking, VFS/TensorFS/Nucleus/Hive data fabric, Aurora graphics, CEF services, security/CI, ISA tooling, and QEMU-oriented tests.

The current refresh adds a unified ISA layer and Linux-inspired kernel architecture crosswalk:

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
       +----------------------+----------------------+
       |         |       |      |      |      |      |
      ISA       MM     SCHED   IRQ    VFS    IPC    NET
       |         |       |      |      |      |      |
   RV/RISC     VM      Tasks   Sys   Tensor Zero   Spotnik
   A64 / x86          Chronos        FS     Copy
                              |
                     AURORA / GPU / CEF
```

The 8192-bit processor remains an architectural/emulation research target, not a claim of existing 8192-bit silicon.

## ISA integration

`include/chimera/unified_isa.hpp` defines a normalized instruction representation for:

- Native Chimera-8192
- RISC-V RV32I/RV64I
- AArch64
- x86-64 CISC

The current decoders intentionally cover stable architectural classes and common instructions. Complete external-ISA conformance requires extension-by-extension tests and is tracked as future work. RISC-V is an open ISA with ratified base and extension specifications; Intel and Arm publish their architectural references, which are linked in `docs/ISA_COMPLETE.md`.

## Kernel architecture integration

`include/chimera/kernel_arch.hpp` and `src/kernel/kernel_arch.cpp` provide the architecture-neutral skeleton for scheduler, virtual memory, IRQ/syscall, VFS/file handles, and packet interfaces. `docs/LINUX_7X_CROSSWALK.md` maps Linux subsystem boundaries to Chimera equivalents.

The requested Bootlin v7.2.2 URL is also encoded as the default root of `tools/kernel_depth_crawler.py`. The crawler supports a ten-level bounded traversal and records access failures instead of silently treating a blocked source as complete.

## Primary source tree

```text
/boot          Spit Fire / Jasper / x86 bootstrap
/kernel        Koronos + scheduler/MM/IPC/net architecture
/include       stable public kernel and ISA headers
/src/isa        native and external-ISA decoders
/src/kernel    architecture-neutral kernel skeleton
/net            Spotnik networking
/userspace      Kore / Aurora / CEF / NDB / Hive
/desktop        Aurora Wayland + GPU shaders
/tools          ISA, source provenance and depth-crawl tooling
/tests          host-side and QEMU-oriented tests
/docs           architecture, provenance and research documentation
/web             browser-based ISA/kernel architecture explorer
```

## Build and test

```bash
cmake -S . -B build -DCHIMERA_ENABLE_EXPERIMENTAL=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

## Web interface

The static architecture explorer is under `web/`. It can be served by any static host:

```bash
python3 -m http.server 8080 --directory web
```

It visualizes ISA families, kernel layers, and the 10-level research crawl model without requiring a backend.

## Research and provenance

Do not vendor external manuals or the Linux kernel wholesale. Use canonical links, clean-room interfaces, generated metadata, and compatible licenses. See:

- `docs/ISA_COMPLETE.md`
- `docs/LINUX_7X_CROSSWALK.md`
- `docs/SOURCE_LICENSE_BOUNDARIES.md`
- `docs/MASTER_SOURCE_MAP.md`
- `docs/PROVENANCE.md`
- `docs/W2K-ASM_IMPORT.md`

## Live demonstrations

- CodeWords technical showcase: https://codewords.agemo.ai/share/html/22980add8f8df4e6c834a970234105a26c98916f152ccff79720c778407fb2ba
- OnHercules live demo: https://chimera-ii-os-730893.onhercules.app/

## License

Repository root is GPL-3.0 unless a file or imported component states otherwise. Third-party and historical source remains subject to its original licensing/provenance requirements.
