# Chimera II ISA — Merged Fetch / Execute / Documentation Specification

## 1. Canonical catalog

The complete internal instruction catalog is stored in `tools/isa/chimera_isa_r8192_complete.csv`. It defines 284 instructions from `0x0001` through `0x011C` with mnemonic, opcode, semantic encoding class, operands, privilege, latency, throughput, pipeline stage, ISA family, notes, and provenance.

The catalog is the authoritative machine-readable metadata source for the supplied R8192, Spotnik, Aurora, VFS, NDB/Hive, and Hybrid system interfaces.

## 2. Fetch and decode

`src/isa/chimera_isa.cpp` now uses a canonical 16-byte host-emulation instruction container:

`opcode[16] | rd[16] | rs[16] | rt[16] | immediate[64]`

The decoder validates instruction length, register indices, and the complete assigned opcode interval. The 16-bit opcode is required because the supplied ISA extends beyond `0x00FF` to `0x011C`.

`run()` advances the program counter by 16 bytes per canonical instruction and rejects truncated streams.

## 3. Execute

The CPU execution core directly implements the base wide arithmetic/control subset currently supported by `CPU8192`: ADD, SUB, AND, OR, XOR, NOT, SHL, SHR, MOV, and comparison operations. The remaining catalog entries are architecturally recognized and form explicit dispatch boundaries for kernel, DMA, networking, VFS, database, GPU/Aurora, security, and service subsystems.

This separation is intentional: privileged operations such as page management, DMA mapping, TPM operations, module loading, reboot, or device configuration must not be implemented as unsafe host side effects inside the pure register execution core. They belong to Koronos/Spotnik/Aurora/VFS/SEC handlers behind capability and privilege checks.

## 4. Pipeline model

```text
FETCH
  |
  v
LENGTH / OPCODE CHECK
  |
  v
DECODE -> normalized Instr
  |
  v
PRIVILEGE + CAPABILITY CHECK
  |
  +---- user arithmetic ----> ALU/MUL -> WRITEBACK
  |
  +---- crypto -------------> CRYPTO backend
  |
  +---- memory/DMA ---------> MM/DMA backend
  |
  +---- Spotnik ------------> network backend
  |
  +---- VFS/DB -------------> filesystem/data backend
  |
  +---- Aurora/GPU ---------> graphics/media backend
  |
  +---- Hybrid SYS/SEC -----> kernel/service boundary
  |
  v
RETIRE / PC ADVANCE
```

The latency and throughput columns in the catalog are architectural scheduling metadata, not measured silicon performance. They should be treated as simulation parameters until a concrete microarchitecture is defined.

## 5. Privilege model

`user` instructions may execute directly when operands/capabilities are valid. `priv` instructions require a kernel or supervisor dispatch path. The emulator must not equate the metadata privilege label with a host OS privilege automatically; the host implementation must enforce the policy explicitly.

## 6. ISA families

- `R8192`: wide arithmetic, memory, comparison and cryptographic primitives.
- `SPOTNIK`: networking, DMA, IOMMU and frame-pool interfaces.
- `AURORA`: GPU, EGL, DMA-BUF, PipeWire, media, presentation and rendering interfaces.
- `VFS`: filesystem and virtual filesystem operations.
- `NDB`: Nucleus database operations.
- `HIVE`: registry/configuration operations.
- `HYBRID`: kernel, security, scheduling, memory, service, observability and platform interfaces.

## 7. Compatibility and provenance

The supplied catalog is original Chimera II project metadata (`source_ref=internal`). It does not reproduce third-party ISA manuals or Linux kernel source. External ISA interoperability remains governed by the canonical external specifications already documented by the project.

## 8. Documentation surfaces

The merged ISA should be exposed consistently in:

- `tools/isa/chimera_isa_r8192_complete.csv` — complete metadata.
- `tools/isa/isa_opcodes.csv` — existing compatibility catalog.
- `include/chimera/isa8192.hpp` — executable instruction ABI.
- `src/isa/chimera_isa.cpp` — fetch/decode/execute implementation.
- `docs/ISA_COMPLETE.md` — external/unified ISA architecture.
- `web/` — browser ISA explorer and visualization.

## 9. Important implementation boundary

A recognized opcode is not automatically a completed subsystem implementation. The CPU core now has a complete recognition/dispatch surface, while subsystem semantics are implemented at their owning kernel or userspace boundary. This prevents the ISA layer from silently performing host filesystem, networking, device, security, or power-management actions.
