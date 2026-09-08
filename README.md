# Chimera II OS

**Research-grade modular operating-system, virtual-processor, desktop, networking, data, and intelligent-computing ecosystem.**

> Status: research/engineering prototype. Host-emulated components are separated from future bare-metal firmware, kernel, driver, FPGA, and silicon targets.

## Architecture baseline

The repository is organized from the **Chimera II OS Developer Guide**: Spit Fire/Jasper boot, Koronos kernel, RegisterN, Spotnik networking, VFS/TensorFS/Nucleus/Hive data fabric, Aurora graphics, CEF services, security/CI, ISA tooling, and QEMU tests. The guide defines this subsystem order and repository skeleton. 

The expanded architecture adds three explicit planes:

```text
                         CHIMERA II
                              |
          +-------------------+-------------------+
          |                   |                   |
     MACHINE PLANE       COGNITIVE PLANE      WORLD PLANE
     R8192 / C8192       128D State           Network / GPU
     RegisterN           Memory               Files / Sensors
     Tensor / Vector     Knowledge            Storage / UI
     Crypto              Reasoning            External APIs
          |                   |                   |
          +-------------------+-------------------+
                              |
                         KORONOS KERNEL
                              |
                           CHIMERA HAL
                              |
                   x86-64 / ARM64 / VM / FPGA
```

The 8192-bit processor is an architectural/emulation research target, not a claim of existing 8192-bit silicon.

## Primary source tree

```text
/boot
  /spitfire                 staged boot material
  /jasper                   boot manager/configuration
  /x86/mbr                  BIOS-compatible SF0 assembly
/kernel
  /include/chimera          kernel ABI headers
  /drivers                  device drivers and DMA glue
  /sched                    Chronos scheduler
  /mm                       memory-management primitives
  /ipc                      zero-copy IPC primitives
/lib
  /registern                width-parametric RegisterN ABI
/net
  /backends/af_xdp          AF_XDP/libxsk integration boundary
  /backends/netmap          Netmap integration boundary
/userspace
  /kore                     service manager
  /aurora                   compositor/desktop
  /spotnik                  networking service
  /ndb                      Nucleus HTAP data layer
  /hive                     hierarchical registry
  /cef                      emulator/service framework
/isa
  /r8192                    8192-bit virtual CPU model
  /c8192                    variable-length instruction model
/tools
  /isa_parser               ISA documentation tooling
  /source_import            provenance/import helpers
/tests
  /unit                     host-side tests
  /qemu_e2e                 boot/integration harnesses
/docs
  Developer Guide and architecture specifications
```

## Implemented host-side core in this refresh

- `RegisterN<Bits>` with 64-bit lane storage, add/subtract/bitwise operations and hex serialization.
- R8192 CPU state and a compact instruction decoder/executor.
- 128D state representation and transition/similarity primitives.
- Chronos resource-aware scheduling score skeleton.
- BootInfo ABI and SF0 BIOS boot sector.
- Zero-copy networking abstraction with a deterministic loopback backend.
- Aurora compositor interface and compute-shader blur prototype.
- Buddy-allocation and lock-free SPSC IPC primitives.
- Hive registry and CEF manifest/capability boundary.

These are intentionally small, testable host prototypes; they are not presented as a production kernel or hardware implementation.

## Build and test

```bash
cmake -S . -B build -DCHIMERA_ENABLE_EXPERIMENTAL=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

Optional tools depend on the host environment: NASM, QEMU, LLVM/Clang, OpenGL/EGL/Wayland development headers, libxsk, Netmap, and a cross compiler.

## Source integration and provenance

The consolidation uses the attached Developer Guide as the primary structural authority, the architecture/research markdown as the higher-level machine/cognitive/world-plane design, and W2K-ASM as **legacy reference material**. The W2K material contains historical Windows/Alpha/PowerPC/x86 assembly and is not treated as a modern API specification. Preserve it under a separately licensed/provenance-aware archive when importing it into a distributable repository.

See:

- `docs/MASTER_SOURCE_MAP.md`
- `docs/PROVENANCE.md`
- `docs/W2K-ASM_IMPORT.md`
- `docs/CHIMERA_II_ARCHITECTURE.md`

## Live demonstrations

- CodeWords technical showcase: https://codewords.agemo.ai/share/html/22980add8f8df4e6c834a970234105a26c98916f152ccff79720c778407fb2ba
- OnHercules live demo: https://chimera-ii-os-730893.onhercules.app/

## Security boundary

Kernel DMA/page-pinning work must enforce capabilities, IOMMU-aware mappings, quotas, complete error unwinding, handle lifetime tracking, and auditability. Do not expose raw physical addresses to untrusted user processes.

## License

The repository root is GPL-3.0 unless a file or imported component states otherwise. Third-party and historical source remains subject to its original licensing/provenance requirements; see `THIRD_PARTY_LICENSES.md`.
