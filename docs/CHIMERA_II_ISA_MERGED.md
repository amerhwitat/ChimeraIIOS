# Chimera II ISA — Merged Fetch / Execute / Documentation Specification

## 1. Canonical catalog

The complete internal instruction catalog is stored in `tools/isa/chimera_isa_r8192_complete.csv`. It defines the canonical semantic instruction identity and opcode assignments.

The catalog is the authoritative machine-readable metadata source for the supplied R8192, Spotnik, Aurora, VFS, NDB/Hive, and Hybrid system interfaces.

The expanded encoding metadata is layered on top of this semantic registry. The newly integrated extension is stored in `tools/isa/isa_extension_0092_011c.csv` and covers the supplied records for `0x0092..0x00EF` and `0x0107..0x011C`.

## 2. Fetch and decode

`src/isa/chimera_isa.cpp` uses a canonical 16-byte host-emulation instruction container:

`opcode[16] | rd[16] | rs[16] | rt[16] | immediate[64]`

The decoder validates instruction length, register indices, and assigned opcode identity. The 16-bit opcode is required because the supplied ISA extends beyond `0x00FF` to `0x011C`.

## 3. Execute

The CPU execution core directly implements the base wide arithmetic/control subset currently supported by `CPU8192`. Catalog entries form explicit dispatch boundaries for kernel, DMA, networking, VFS, database, GPU/Aurora, security, media, and service subsystems.

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
  +---- Aurora/GPU/media ---> graphics/media backend
  +---- Hybrid SYS/SEC -----> kernel/service boundary
  |
  v
RETIRE / PC ADVANCE
```

Latency and throughput are architectural scheduling metadata, not measured silicon performance.

## 5. Expanded encoding layer

`tools/isa/isa_opcodes_expanded_with_encodings.csv` provides encoding-aware metadata for the earlier expanded catalog. The new `tools/isa/isa_extension_0092_011c.csv` adds the supplied Aurora and Hybrid records through `0x011C`.

These fields are **illustrative tooling templates**, not canonical hardware encodings. The current emulator continues to normalize native instructions into its 16-byte host packet. Longer or shorter logical encodings require an explicitly defined extension mechanism before becoming normative.

### Integrated extension ranges

- `0x0092..0x00AC`: Aurora PipeWire, audio/video, GPU, shader, texture, PBO and rendering operations.
- `0x00AD..0x00B4`: Aurora presentation notification, acknowledgement, cancellation, query, mode and priority operations.
- `0x00B5..0x00C3`: Hybrid VirtIO, PCI, MSI, BAR and DMA operations.
- `0x00C4..0x00EF`: Hybrid memory, lifecycle, synchronization, PMU, tracing, thermal, certificate, keystore and audit operations.
- `0x0107..0x011C`: Hybrid configuration, licensing, metrics, cluster, service, diagnostics, maintenance and security-scan operations.

The supplied source intentionally does not define `0x00F0..0x0106` in this extension, so no missing records are fabricated.

### Encoding conformance observations

Several supplied templates require review before normative binary encoding:

1. `ECC_POINT_ADD (0x0043)` specifies `rt in separate field` without defining its exact bit position, width or serialization order.
2. Some opcodes above `0x00FF` have templates with an 8-bit opcode field even though their opcode identity is 16-bit, for example `0x0107` and `0x011C`. Such templates cannot represent those opcode values in an 8-bit field.
3. Fields marked `separate field` are preserved as metadata and are not silently packed into the canonical 16-byte ABI.
4. Example binary values are preserved as supplied and must be treated as illustrative vectors until automated round-trip validation is available.

See `docs/ISA_EXTENSION_0092_011C.md` for the detailed extension and conformance policy.

## 6. Privilege model

`user` instructions may execute directly when operands/capabilities are valid. `priv` instructions require a kernel or supervisor dispatch path. The host implementation must enforce the policy explicitly.

The extension contains privileged operations affecting caches, TLBs, page tables, PCI, DMA, power state, reboot/shutdown, keystores, security scans and maintenance mode. These remain capability-gated subsystem operations rather than unrestricted register-core side effects.

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

A recognized opcode is not automatically a completed subsystem implementation. The CPU core provides the recognition/dispatch surface, while subsystem semantics are implemented at their owning kernel or userspace boundary. This prevents the ISA layer from silently performing host filesystem, networking, device, security, power-management, media, or graphics actions.
