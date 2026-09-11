# Chimera II OS Implementation Roadmap

## Status

This roadmap is the execution baseline for the Computer Edition/Koronos and the separately isolated Mobile Microkernel edition. The project remains a research/engineering prototype: host validation and emulation are distinct from future bare-metal hardware targets.

## Phase 1 — Repository and source baseline

- [x] Separate Computer and Mobile kernel implementations.
- [x] Establish `library/` reference/provenance layout.
- [x] Keep third-party source, binaries, firmware and proprietary material out of production targets unless licensing and redistribution rights are established.
- [x] Add build/test entry points for the main repository and Mobile Microkernel.

## Phase 2 — Canonical ISA and N-bit runtime

- [x] Align the canonical R8192/C8192 opcode catalog with the low-level specification.
- [x] Cover NOP, arithmetic, bitwise, shifts, memory, vector/tensor, networking, synchronization, task, system-call and control-flow groups in the catalog.
- [x] Extend `WideInt` with subtraction, AND, OR, left shift and right shift while preserving width normalization.
- [x] Add a dedicated CTest target for extended N-bit runtime operations.
- [x] Extend ISA test-vector generation with canonical operations and deterministic scalar golden results.
- [ ] Complete executable instruction dispatch for every catalog entry; catalog presence is not equivalent to implemented execution semantics.
- [ ] Add generated conformance vectors for every supported encoding format.

The low-level specification defines R8192 as a fixed 64-bit instruction-word architecture and C8192 as variable packets from 64 through 4096 bits; it also distinguishes architectural register width from encoding width, execution lanes, issue width and physical throughput. See `library/provenance/INDEX.md` and the imported low-level specifications.

## Phase 3 — Koronos kernel

- [ ] Complete architecture-context save/restore and privileged trap paths for each supported host architecture.
- [ ] Integrate scheduler policy modules and per-CPU run queues.
- [ ] Harden IPC, shared-memory queues, guard pages, slab caches and RCU paths.
- [ ] Keep VFS, networking, databases and compatibility services outside the privileged core where practical.

## Phase 4 — Mobile Microkernel

- [x] Dedicated `Mobile Microkernel/` source tree.
- [x] AArch64-first and RISC-V64 secondary porting model.
- [x] Power, thermal, suspend/resume, capability and driver-service interfaces.
- [ ] Implement hardware exception/vector entry, MMU/page tables and context switching.
- [ ] Add GIC/timer integration and device-tree/firmware handoff.
- [ ] Add SoC HALs, IOMMU/DMA, display, input, storage, audio, camera, sensors, USB, Wi-Fi, Bluetooth and cellular service boundaries.

## Phase 5 — Memory and DMA

- [ ] Complete buddy/slab allocation paths and NUMA-aware policy where applicable.
- [ ] Expand the architecture-neutral memory bus profiles.
- [ ] Harden DMA pinning, scatter-gather, IOMMU mappings and completion queues.
- [ ] Add negative tests for invalid physical-address descriptors and capability violations.

## Phase 6 — Spotnik networking

- [ ] Finish dual-stack IPv4/IPv6 service boundaries.
- [ ] Integrate zero-copy packet ownership with DMA descriptors.
- [ ] Add AF_XDP/Netmap adapters where the host supports them.
- [ ] Add event-driven completion queues and interface capability probing.

## Phase 7 — Aurora desktop

- [ ] HDR/bloom/volumetric-lighting research path.
- [ ] GPU-backed blur/compositor effects.
- [ ] Workspace switching and desktop personality layer.
- [ ] Preserve a host-safe OpenGL/Wayland implementation independent of future native GPU drivers.

## Phase 8 — Compatibility and toolchains

- [ ] Expand architecture adapters for x86-64, AArch64, RISC-V64, MIPS64, POWER64, SPARC64, s390x, 68k, Alpha, PA-RISC, SuperH, Itanium, AVR, Xtensa and WebAssembly.
- [ ] Maintain foreign-ISA-to-canonical-micro-op boundaries rather than mixing foreign opcodes into the native architectural state.
- [ ] Integrate assembler/disassembler/compiler/linker/debugger adapters.
- [ ] Keep Microsoft and proprietary vendor tools as external adapters unless redistribution is permitted.

## Phase 9 — Nucleus and Hive

- [ ] Expand neural/model/tensor/embedding/graph storage APIs.
- [ ] Add checkpoint and trusted-node synchronization audit trails.
- [ ] Keep executable-code exchange disabled by default in trusted-node synchronization.
- [ ] Add backend adapters without copying third-party database source trees.

## Phase 10 — Boot and ISO

- [ ] Produce reproducible BIOS/MBR and UEFI image pipelines.
- [ ] Add secure/verified boot metadata and explicit firmware handoff records.
- [ ] Package kernel, runtime, libraries and required executables into bootable images.
- [ ] Add VM smoke images before claiming hardware boot readiness.

## Phase 11 — Verification

- [ ] CTest/CMake host builds on Linux and Windows/MSVC.
- [ ] Python validation for registries and generated ISA metadata.
- [ ] Emulator golden vectors and property tests.
- [ ] Driver Verifier / Windows harness where applicable.
- [ ] VM boot tests and reproducible ISO checksums.

## Phase 12 — Documentation and release engineering

- [ ] Doxygen API documentation.
- [ ] Architecture and data-flow diagrams.
- [ ] Installer and deployment guides.
- [ ] Changelogs with explicit distinction between implemented, emulated and planned hardware features.
- [ ] Release manifests containing source provenance and license metadata.

## Engineering rule

A catalog, interface, research document or emulator is not evidence that a physical feature exists. Hardware-dependent claims require an implementation and a reproducible measurement. The imported research specification explicitly separates instruction encoding width, register width, execution lanes, issue width and physical throughput.
