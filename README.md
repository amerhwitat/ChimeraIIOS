# Chimera II OS

**Research-grade modular operating-system, virtual-processor, desktop/mobile, networking, data and intelligent-computing ecosystem.**

> Status: public research/engineering prototype. Host-emulated components are separated from future bare-metal firmware, kernel, driver, FPGA, mobile-hardware and silicon targets.

## Editions

Chimera II OS now has two explicitly separated kernel implementations:

- **Computer Edition / Koronos** — general computer, workstation, server and desktop-oriented kernel implementation.
- **Mobile Edition / Mobile Microkernel** — dedicated mobile kernel implementation under `Mobile Microkernel/`, primarily targeting AArch64 mobile SoCs with a RISC-V64 porting path.

The Mobile Microkernel shares stable interfaces and concepts with the wider Chimera architecture, but does not inherit desktop/server scheduling, boot, driver or UI assumptions. It adds mobile-specific energy-aware scheduling, heterogeneous CPU support, thermal coordination, suspend/resume, mobile boot/verified-boot boundaries and capability-isolated driver services.

## Cognitive and trusted-node fabric

Chimera II includes a local-first hybrid cognitive runtime: 128D state representation, RNN/GRU/LSTM temporal memory, transformer attention, retrieval-augmented generation, graph memory, planning and policy-controlled tool execution. Nucleus stores neural models, tensors, embeddings, memories, graph relations, checkpoints, trusted-node identities and synchronization events. This architecture is an engineering target, not a claim of guaranteed general intelligence.

Trusted Chimera nodes synchronize only after cryptographic identity verification, signed capabilities, mutual authentication, replay protection, sequence validation, content-addressed records and revocation checks. Nodes exchange signed knowledge/model metadata/checkpoints rather than arbitrary executable code. Unsigned model replacement and remote code execution are prohibited.

Internet discovery uses published endpoints only: signed bootstrap directories, DNS SRV/TXT, local mDNS/Bonjour and operator-supplied peers. Chimera does not perform unsolicited Internet port scanning. See `docs/NEURAL_TRUSTED_NODE_FABRIC.md`.

## Neural database — Nucleus

`database/manifests/neural-network-database.yaml` defines durable neural-network information storage for model metadata, tensor shards, embeddings, semantic memories, graph nodes/edges, training runs, trusted peers and synchronization audit events. Nucleus remains a userspace HTAP service and can use the existing database backend integration layer.

## Universal ISA and CPU compatibility

Chimera II uses a layered universal-ISA model. Native C8192/R8192 instructions remain the canonical architecture, while x86-64, AArch64, RISC-V, MIPS64, POWER64, SPARC64, IBM Z/s390x, Motorola 68k, Alpha, PA-RISC, SuperH, Itanium, AVR, Xtensa and WebAssembly are represented as compatibility targets. Foreign instructions are decoded into canonical micro-operations and mapped to `RegisterN<N>` state.

## Universal CPU toolchains and virtual memory bus

`toolchains/registry.json` records assembler, disassembler, compiler, linker, object-tool, debugger and emulator capabilities for major open toolchain families including GNU Binutils/GAS/objdump, GCC, LLVM MC/Clang/LLD, NASM/YASM and QEMU. Microsoft MASM/MSVC and vendor compiler families are represented as external adapters rather than redistributed binaries.

Koronos has an architecture-neutral virtual memory bus in `include/chimera/memory_bus.hpp`. `memory/bus-profiles.json` records address width, transaction width, endianness, ordering, coherency, cache-line, DMA/IOMMU and inspection metadata. `memory_bus_probe` consumes safe firmware/device-tree/ACPI/hypervisor descriptors and does not dereference arbitrary host physical addresses.

## Database subsystem

Koronos exposes a userspace database-service boundary for Nucleus/Hive and applications. Supported open-source integration targets include MariaDB Community Server, PostgreSQL, SQLite, DuckDB, RocksDB, LevelDB, Valkey, Apache Cassandra and Apache CouchDB. The repository contains original adapters/manifests rather than copying third-party source trees or binaries.

## Koronos microkernel 2

The computer kernel has an explicit architecture-context and service registry layer. Wide `RegisterN<8192>` state is lazy. Database, networking, VFS, virtualization and compatibility execution remain userspace/service boundaries where practical; the kernel handles capabilities, IPC, scheduling, memory and privileged traps.

## Mobile Microkernel

`Mobile Microkernel/` is the dedicated mobile implementation. Its privileged core is intentionally small: boot handoff, exception/interrupt dispatch, capability enforcement, address-space primitives, IPC, preemptive scheduling, CPU idle/hotplug coordination and power/thermal hooks. Mobile drivers and policy-heavy services remain isolated behind explicit service boundaries.

Primary target: AArch64. Secondary target: RISC-V64. Planned mobile driver families include display, touchscreen, GPU/accelerator, audio, camera, sensors, storage, USB, Bluetooth, Wi-Fi, cellular, power and IOMMU/DMA. See `Mobile Microkernel/docs/ARCHITECTURE.md` and `Mobile Microkernel/docs/PORTING.md`.

## Language matrix

| Language / toolchain | Role |
|---|---|
| C / C++ | Kernel, ISA, boot, native desktop/mobile and hardware-facing implementation |
| Visual C++ / MSVC | Windows-native bootstrap and host integration |
| C# / F# / VB.NET | Managed services and tooling |
| Java | JVM interoperability and service bridge |
| Node.js | Web/integration runtime |
| Python | Reference research, ML/RL and data-processing |

## Architecture baseline

```text
CHIMERA II OS
  |
  +-- MACHINE: R8192 / C8192 / RegisterN / Tensor / Vector
  +-- COGNITIVE: 128D + RNN/GRU/LSTM + Attention + RAG + Graph Memory
  +-- TRUST FABRIC: identities + capabilities + signed synchronization
  +-- NUCLEUS: neural/model/vector/graph/HTAP database
  +-- WORLD: network / GPU / files / sensors / storage / UI
  +-- KERNEL EDITIONS
       |
       +-- COMPUTER: KORONOS
       |     +-- x86-64 / ARM64 / RISC-V
       |     +-- desktop/server scheduling and services
       |
       +-- MOBILE: MOBILE MICROKERNEL
             +-- AArch64 / RISC-V64
             +-- energy + thermal aware scheduling
             +-- suspend/resume + mobile power
             +-- verified-boot + capability-isolated drivers
  +-- SPIT FIRE + JASPER: boot and boot-manager layers
  +-- AURORA / GPU / CEF / WEB
  +-- APP CENTER + PACKAGE MANAGER
```

## Build and test

Computer edition:

```bash
cmake -S . -B build -DCHIMERA_ENABLE_EXPERIMENTAL=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

Mobile microkernel host validation:

```bash
cmake -S "Mobile Microkernel" -B build-mobile
cmake --build build-mobile --parallel
ctest --test-dir build-mobile --output-on-failure
```

Additional repository validation:

```bash
python3 tools/toolchain/validate_registry.py
python3 tools/memory/validate_profiles.py
python3 -m pytest -q tests/boot tests/iso tests/isa tests/database
cd boot/iso && ./build-iso.sh
```

See `Mobile Microkernel/README.md`, `Mobile Microkernel/docs/ARCHITECTURE.md`, `Mobile Microkernel/docs/BOOT.md`, `Mobile Microkernel/docs/SECURITY.md`, `Mobile Microkernel/docs/POWER_MANAGEMENT.md`, `Mobile Microkernel/docs/MEMORY.md`, `Mobile Microkernel/docs/SCHEDULER.md`, `Mobile Microkernel/docs/IPC.md`, `Mobile Microkernel/docs/DRIVERS.md` and `Mobile Microkernel/docs/PORTING.md`.
