# Chimera II OS — Deep Gap, Standards and Implementation Audit

**Audit date:** 2026-09-08  
**Repository:** `amerhwitat/ChimeraIIOS`  
**Architecture status:** research-grade host implementation with explicit bare-metal gaps

## 1. Executive result

The repository has a coherent ISA/toolchain/web/installer foundation, but it is not yet a bootable independent OS. The highest-value gaps are below:

| Area | Current state | Required implementation | Priority |
|---|---|---|---|
| R8192 decode ABI | interpreter + metadata | canonical 16-byte fetch contract and strict conformance | P0 |
| Koronos scheduler | previous queue stub | deterministic priority scheduler and task state transitions | P0 |
| Virtual memory | previous map stub | page-aligned mapping metadata and range validation | P0 |
| Boot ABI | design documents/stubs | versioned, CRC-protected handoff structure | P0 |
| DMA/IOMMU | ISA opcodes and architecture | ownership-aware DMA mapping model with explicit sync/unmap | P0 |
| IOMMUFD model | not implemented | capability-oriented userspace/device-memory interface | P1 |
| PCI/PCIe driver layer | inventory/standards only | device lifecycle, BAR mapping, MSI/MSI-X and DMA attachment | P1 |
| UEFI loader | stub/design | PE/COFF loading, memory map, framebuffer, ExitBootServices retry | P1 |
| Interrupt/timer | syscall/kernel stubs | APIC/IOAPIC/HPET/TSC or architecture-neutral HAL | P1 |
| ELF loader | absent as a complete runtime | ELF64 validation, mapping, relocations, entry handoff | P1 |
| Network stack | architecture/scaffold | Ethernet + IPv4/IPv6 + UDP/TCP + routing + zero-copy ownership | P1 |
| Aurora | design/Wayland adapter | DRM/KMS or equivalent backend, dma-buf lifecycle, input and presentation | P1 |
| LLVM backend | planned | TargetMachine, register classes, MC layer, assembler/disassembler | P1 |
| TensorFS/Nucleus | scaffold | durable format, WAL/recovery, crash consistency and query execution | P2 |
| Hive | in-memory model | durable transactional registry and schema migration | P2 |
| CEF/compatibility | integration plan | sandboxed runtime boundary and executable loader | P2 |
| FPGA R8192 | research target | banked 128×64-bit datapath and measured validation | P3 |

The attached research material independently identifies complete page tables, interrupt controllers, allocator, ELF loader, UEFI loader, LLVM backend, real NIC DMA/TCP, compositor and FPGA implementation as major future work. fileciteturn58file0L30-L35

## 2. Repository/library reconciliation

The library architecture describes Chimera II as Spit Fire → Jasper → Koronos → Kore/services → Aurora, with Spotnik, Nucleus, Hive and CEF as subsystem boundaries. fileciteturn57file0L20-L32

The research implementation matrix previously classified RegisterN as implemented, R8192/C8192 as partial interpreter, boot as stub, Koronos as host scheduler scaffold, Spotnik as packet-ownership scaffold, Aurora as design-only, Nucleus as WAL/KV scaffold and Hive as in-memory. fileciteturn58file1L56-L71

This audit therefore avoids falsely representing the research blueprint as a finished bare-metal OS.

## 3. ISA corrections and contract

The repository's native interpreter now treats the instruction fetch packet as the canonical 16-byte ABI: 16-bit opcode, three 16-bit register fields and a 64-bit immediate/reserved tail. Short 8-byte packets are rejected by the native decoder.

The defined opcode interval remains `0x0001..0x011C` (284 instructions). `0x0000` is intentionally not part of the defined catalog even though a legacy `OP_NOP` constant remains for source compatibility.

The execution core must continue to distinguish:

1. syntactically decodable;
2. catalog-defined;
3. privilege/capability permitted;
4. directly executable by the pure register core;
5. routed to a subsystem backend;
6. unsupported/unbound service.

A recognized opcode must never be treated as proof that the corresponding OS service is implemented.

## 4. Kernel correctness requirements

### Scheduler

The scheduler now has explicit `Ready`, `Running`, `Blocked`, `Sleeping` and `Terminated` states, deterministic priority selection, virtual runtime accounting and wake/block/yield transitions. This is still a host model, not an SMP scheduler.

Next required work:

- per-CPU queues;
- timer-driven preemption;
- interrupt-safe run-queue operations;
- CPU affinity;
- priority inheritance/ceiling for kernel locks;
- wait queues and futex-like primitives;
- SMP IPI/work stealing;
- deterministic replay hooks.

### Virtual memory

The host memory model now tracks page-aligned virtual/physical mappings and validates ranges. It is not a hardware page-table implementation.

Next required work:

- x86-64 4/5-level page tables;
- ARM64 translation tables;
- ASID/PCID handling;
- TLB shootdown;
- copy-on-write;
- guard pages;
- user/kernel W^X;
- NUMA policy;
- huge-page policy;
- memory pressure/reclaim.

## 5. DMA/IOMMU model

A new host-side DMA manager models buffer ownership, device DMA masks, mapping tokens, synchronization and mandatory unmap. This is deliberately stricter than simply passing host pointers to a device.

This follows modern driver principles: DMA addresses are not CPU virtual addresses, IOMMU translation may exist, and DMA mappings must be paired with correct unmapping/lifetime rules. Linux's current DMA documentation explicitly warns that mapping violations can cause data corruption and emphasizes the distinction among virtual, physical and DMA addresses. citeturn1search2turn1search6

Linux's current VFIO documentation also identifies IOMMUFD as the forward-looking userspace interface for advanced DMA/I/O page-table management. citeturn1search4

Chimera should therefore evolve toward:

`device → capability → I/O address space → DMA mapping → ownership → completion → sync/unmap`

rather than exposing arbitrary physical addresses to services.

## 6. PCI/driver gap

The driver layer needs a first-class lifecycle:

`discover → match → enable → BAR map → MSI/MSI-X → DMA domain → device init → runtime → quiesce → unmap → disable`

The current Linux driver documentation provides a useful interoperability reference for PCI support, hotplug, P2P DMA and device lifecycle without implying that Chimera should copy Linux internals. citeturn1search0turn1search1

P2P DMA must remain explicitly topology-aware; Linux documents that PCIe P2P safety depends on the route, ACS and hierarchy. citeturn1search8

## 7. Boot and firmware gap

UEFI 2.11 and ACPI 6.6 are the current baseline identified by the UEFI Forum. citeturn0search2

Chimera's UEFI path should implement:

1. PE/COFF image validation;
2. filesystem discovery;
3. kernel/initrd loading;
4. UEFI memory-map acquisition;
5. framebuffer/GOP discovery;
6. ACPI RSDP discovery;
7. Secure Boot/measured-boot metadata capture;
8. `ExitBootServices()` retry after obtaining the final memory map;
9. construction of the versioned `BootInfo` ABI;
10. immutable handoff to Koronos.

The new BootInfo structure provides the software contract; firmware integration remains future work.

## 8. Aurora / Wayland / graphics

The Aurora design should target current Wayland protocol semantics instead of creating a private incompatible window protocol. Wayland is asynchronous, object-oriented and message based, with protocol interfaces generated from XML. citeturn2search0turn2search8

As of June 2026, Wayland protocols 1.49 are released. citeturn2search3

The graphics backend should therefore prioritize:

- Wayland core object model;
- xdg-shell;
- linux-dmabuf;
- explicit buffer ownership/release;
- presentation timing;
- input/seat/keyboard/pointer/touch;
- PipeWire media boundary;
- Vulkan/OpenGL abstraction.

The current Vulkan documentation site reports Vulkan 1.4.361 generated 2026-09-03. citeturn1search3

## 9. Networking gap

The target architecture remains IPv6-first dual-stack with TCP/UDP/QUIC compatibility. Happy Eyeballs v2 should be implemented rather than merely documented; RFC 8305 defines concurrent asynchronous resolution/connection establishment while preferring IPv6. citeturn2search6turn2search7

Required layers:

`NIC → DMA rings → Ethernet → ARP/NDP → IPv4/IPv6 → ICMP → UDP/TCP → routing → sockets → services`

and an optional QUIC user/service boundary.

## 10. Security gap

The architecture already calls for Secure Boot, measured images, TPM, W^X, capability-checked syscalls, protected MMIO, IOMMU isolation, explicit network-buffer ownership, least privilege and reproducible builds. fileciteturn58file7L587-L602

The implementation gap is to turn these into enforceable invariants:

- capability objects with non-forgeable handles;
- syscall argument/range validation;
- device capability delegation;
- DMA domain isolation;
- signed module manifest;
- measured boot event log;
- key rotation and revocation;
- audit records with stable event IDs;
- fuzzing for decoders and parsers;
- deterministic build metadata.

## 11. Standards baseline for the next implementation cycle

- UEFI 2.11 / ACPI 6.6. citeturn0search2
- Linux driver/DMA/IOMMUFD documentation as interoperability/reference material. citeturn1search0turn1search2turn1search4
- Wayland core and wayland-protocols 1.49. citeturn2search0turn2search3
- Vulkan 1.4.361 current documentation snapshot. citeturn1search3
- RFC 8305 Happy Eyeballs v2 for dual-stack connection establishment. citeturn2search6
- Existing project references for GPT/ESP, virtio, NVMe, POSIX-like interfaces, OpenZFS and compatibility layers.

## 12. Engineering rule

Chimera II remains a clean-room research OS. External standards are implemented as protocols/contracts; external kernel source is not copied into the project. Every future imported dependency must record its license, version, provenance and compatibility boundary.

## 13. Next execution order

**P0:** ISA ABI → BootInfo → scheduler → VM → DMA ownership.  
**P1:** interrupts/timers → UEFI loader → ELF loader → PCI/device model → network core → Aurora backend.  
**P2:** LLVM backend → durable VFS/Nucleus/Hive → CEF sandbox → compatibility services.  
**P3:** QEMU boot target → FPGA banked R8192 datapath → measured performance.

This sequence preserves the project's central 128D model while converting the current architecture from a collection of scaffolds into a progressively bootable and testable system.
