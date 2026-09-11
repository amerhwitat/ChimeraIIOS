# External Building-Block Research

## Library-derived architecture

The Library research corpus identifies a modular stack: firmware/boot, Koronos microkernel, VM/VFS/IPC, Spotnik networking, Aurora desktop, Nucleus/Hive data services, CEF compatibility, RegisterN/R8192, mobile/robotics V-Cores, DMA/zero-copy paths, and an emulator-first validation strategy. The implementation added in `building_blocks/` expresses these as small C++ contracts.

## Public technical references reviewed

- Linux kernel documentation: scheduler, locking, driver APIs, networking, memory management and zero-copy are useful behavioral/reference sources. The repository must preserve the license of any imported Linux file and must not treat the whole Linux tree as Chimera-owned code.
- RISC-V ratified specifications: the current public library includes unprivileged and privileged ISA material and ratified extensions. Chimera's foreign-ISA layer therefore treats RISC-V privilege/trap behavior as an adapter target rather than copying the specification into executable code.
- UEFI Forum: UEFI 2.11 and ACPI 6.6 are current reference points. UEFI states that specification reproduction/implementation requires the applicable membership/license terms, so this repository records the interface and uses licensed implementation sources rather than copying the specification text.
- LLVM: the established compiler-backend model supports multiple host targets and provides the realistic path for a future Chimera backend: frontend -> IR -> target lowering -> object/linker.

## Import policy

1. Native Chimera implementation is preferred for kernel-critical interfaces.
2. Compatible open-source code may be imported only after file-level license/provenance review.
3. Public standards are used as behavioral references; copyrighted specifications are not bulk-copied into source files.
4. Proprietary, leaked, confidential or trade-secret Windows code is never imported.
5. Large third-party projects are integrated through adapters, manifests and clean-room interfaces rather than indiscriminately copied.
6. Research prototypes are labelled as such and do not imply existing silicon or production hardware.

## Research-to-code mapping

| Research building block | Chimera implementation |
|---|---|
| Boot ABI | `building_blocks/boot/boot_info.hpp` |
| VM/DMA | `building_blocks/memory/memory_contract.hpp` |
| Scheduler/RT | `building_blocks/kernel/scheduler_contract.hpp` |
| Capability IPC | `building_blocks/kernel/ipc_contract.hpp` |
| Zero-copy networking | `building_blocks/networking/Spotnik/packet_contract.hpp` |
| RegisterN/micro-ops | `building_blocks/runtime/registern_runtime.hpp` |
| Foreign ISA | `building_blocks/compatibility/foreign_arch.hpp` |
| Nucleus | `building_blocks/database/Nucleus/record_contract.hpp` |
| Hive | `building_blocks/database/Hive/registry_contract.hpp` |
| Mobile/robotics V-Cores | `building_blocks/robotics/vcore_contract.hpp` |
| Aurora | `building_blocks/desktop/Aurora/surface_contract.hpp` |
| ISA metadata | `building_blocks/tools/isa/core_opcode_table.cpp` |

This is the first implementation pass; it intentionally creates stable seams for subsequent drivers, real MMU/context switching, network protocols, filesystems, compiler backends and hardware ports.
