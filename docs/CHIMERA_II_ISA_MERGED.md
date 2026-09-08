# Chimera II ISA — Merged Fetch / Execute / Documentation Specification

## 1. Canonical catalog

The complete internal instruction catalog is stored in `tools/isa/chimera_isa_r8192_complete.csv`. It defines 284 instructions from `0x0001` through `0x011C` with mnemonic, opcode, semantic encoding class, operands, privilege, latency, throughput, pipeline stage, ISA family, notes, and provenance.

The catalog is the authoritative machine-readable metadata source for the supplied R8192, Spotnik, Aurora, VFS, NDB/Hive, and Hybrid system interfaces.

## 2. Fetch and decode

`src/isa/chimera_isa.cpp` uses a canonical 16-byte host-emulation instruction container:

`opcode[16] | rd[16] | rs[16] | rt[16] | immediate[64]`

The decoder validates instruction length, register indices, and the complete assigned opcode interval. The 16-bit opcode is required because the supplied ISA extends beyond `0x00FF` to `0x011C`.

## 3. Execute

The CPU execution core directly implements the base wide arithmetic/control subset currently supported by `CPU8192`. Remaining catalog entries are architecturally recognized and form explicit dispatch boundaries for kernel, DMA, networking, VFS, database, GPU/Aurora, security, and service subsystems.

Execution status is explicit: `Executed`, `PrivilegeViolation`, `InvalidOpcode`, or `UnimplementedService`.

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
  +---- crypto -------------> CRYPTO backend
  +---- memory/DMA ---------> MM/DMA backend
  +---- Spotnik ------------> network backend
  +---- VFS/DB -------------> filesystem/data backend
  +---- Aurora/GPU ---------> graphics/media backend
  +---- Hybrid SYS/SEC -----> kernel/service boundary
  |
  v
RETIRE / PC ADVANCE
```

Latency and throughput are architectural scheduling metadata, not measured silicon performance.

## 5. Expanded encoding layer

`tools/isa/isa_opcodes_expanded_with_encodings.csv` provides encoding-aware metadata including `encoding_template`, `opcode_bits`, `imm_size`, `modrm_like`, and `example_binary`.

These fields are **illustrative tooling templates**, not canonical hardware encodings. The current emulator continues to normalize native instructions into its 16-byte host packet. Longer or shorter logical encodings require an explicitly defined extension mechanism before becoming normative.

The supplied encoding source in the project discussion is truncated during the `RSAMOD` record. Missing records are intentionally not fabricated. The existing 284-opcode semantic registry remains authoritative for instruction identity until the complete encoding source is supplied and validated.

See:

- `docs/ISA_ENCODING_SPEC.md`
- `docs/ISA_ENCODING_MIGRATION.md`
- `docs/ISA_ENCODING_CONFORMANCE.md`
- `docs/ISA_ENCODING_DATA_DICTIONARY.md`

## 6. Privilege model

`user` instructions may execute directly when operands/capabilities are valid. `priv` instructions require a kernel or supervisor dispatch path. The host implementation must enforce the policy explicitly.

## 7. ISA families

- `R8192`: wide arithmetic, memory, comparison and cryptographic primitives.
- `SPOTNIK`: networking, DMA, IOMMU and frame-pool interfaces.
- `AURORA`: GPU, EGL, DMA-BUF, PipeWire, media, presentation and rendering interfaces.
- `VFS`: filesystem and virtual filesystem operations.
- `NDB`: Nucleus database operations.
- `HIVE`: registry/configuration operations.
- `HYBRID`: kernel, security, scheduling, memory, service, observability and platform interfaces.

## 8. Compatibility and provenance

The supplied catalog is original Chimera II project metadata (`source_ref=internal`). It does not reproduce third-party ISA manuals or Linux kernel source. External ISA interoperability remains governed by canonical external specifications.

## 9. Implementation boundary

A recognized opcode is not automatically a completed subsystem implementation. The CPU core provides the recognition/dispatch surface, while subsystem semantics are implemented at their owning kernel or userspace boundary. This prevents the ISA layer from silently performing host filesystem, networking, device, security, or power-management actions.
