# Universal CPU Toolchains and Virtual Memory Bus Design

## Goal
Extend Chimera II OS with a provenance-aware registry for assemblers, disassemblers, compilers, linkers and emulators across supported CPU families, and add a virtual memory-bus layer that models the architectural properties Chimera can discover at boot/runtime.

## Design
Chimera separates toolchain compatibility from CPU execution. A target entry records the assembler/disassembler/compiler/linker/debugger/emulator families that can service it; the OS may invoke an installed tool through a detected capability rather than assuming every historical vendor tool is present. Proprietary tools are represented as external adapters, not redistributed.

The memory-bus layer is a virtual interconnect contract. It records address width, data width, endianness, transaction ordering, cache-line size, coherency model, NUMA/topology information, DMA/IOMMU capabilities, MMIO windows and architectural inspection sources. A probe consumes hardware/firmware/virtual-machine descriptors and selects a compatible VirtualBusProfile. It does not pretend that a generic host can expose undocumented physical wiring.

The virtual bus is architecture-neutral at its API boundary and architecture-specific through profiles for x86/x86-64, ARM/AArch64, RISC-V, POWER, MIPS, SPARC, s390x, Alpha, PA-RISC, SuperH, m68k, Itanium, AVR, Xtensa, LoongArch, OpenRISC, MicroBlaze, TriCore, RX, Hexagon and other registered targets as evidence is added. RegisterN-backed payloads may be wider than the physical bus; bus transactions therefore carry a byte width plus optional wide-lane metadata rather than treating an 8192-bit register as a physical 8192-bit motherboard bus.

## Toolchain coverage policy
The registry covers major open toolchain families (GNU Binutils/GAS/objdump, GCC, LLVM/Clang/LLD/LLVM MC, NASM/YASM where applicable, and QEMU system/user emulation) and records vendor/proprietary families as adapters where licensing or availability prevents redistribution. It is explicitly a compatibility catalog, not a claim that every CPU ever manufactured is implemented in-tree.

## Runtime inspection
At boot, Koronos may collect architecture identity, physical/virtual address width, memory-map descriptors, cache/coherency properties, DMA/IOMMU information, firmware tables and hypervisor-provided topology. The probe produces a deterministic snapshot that can be serialized for ISO/diagnostic manifests. The virtual bus uses this snapshot to select transaction constraints and route memory, MMIO and DMA requests.

## Safety and compatibility
- Existing C8192/R8192 ISA encodings and the 16-byte canonical semantic ABI remain unchanged.
- Toolchain entries never imply native execution; foreign ISAs remain translated/emulated/imported.
- Memory access validation occurs before routing; overflow and address-width violations are rejected.
- MMIO is explicitly typed and never treated as ordinary RAM.
- DMA requires a device aperture and optional IOMMU translation domain.
- Endianness and ordering are properties of the bus profile and transaction, not global assumptions.
- ISO-Tool stages manifests and provenance, not unlicensed proprietary binaries.
