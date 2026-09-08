# Chimera II ISA Extension — 0x0092..0x011C

## Scope

This extension integrates the supplied ISA metadata for opcodes `0x0092..0x00EF` and `0x0107..0x011C` into the Chimera II ISA metadata layer.

The source records are preserved in:

- `tools/isa/isa_extension_0092_011c.csv`

The extension is additive. It does not renumber existing opcodes and does not replace the canonical 16-byte emulator instruction container.

## Functional coverage

| Range | Primary subsystem | Coverage |
|---|---|---|
| `0x0092..0x00AC` | Aurora | PipeWire, audio/video, GPU, shaders, textures, PBO, rendering and presentation |
| `0x00AD..0x00B4` | Aurora | Wayland-style presentation notifications, acknowledgement, cancellation, query and priority/mode controls |
| `0x00B5..0x00C3` | Hybrid | VirtIO, PCI configuration, MSI, BAR mapping and DMA |
| `0x00C4..0x00EF` | Hybrid | persistent/kernel/user memory, power lifecycle, PMU, tracing, synchronization, TLB, SMP, thermal and security/keystore/audit interfaces |
| `0x0107..0x011C` | Hybrid | configuration, licensing, metrics, cluster, service, diagnostics, maintenance and security scanning |

## Decoder and execution policy

All entries use the existing ISA pipeline:

`FETCH -> LENGTH/OPCODE CHECK -> DECODE -> PRIVILEGE + CAPABILITY CHECK -> subsystem dispatch -> RETIRE/PC ADVANCE`

A metadata entry is a recognized instruction definition; it is not proof that the corresponding kernel/device service is implemented. Host-side effects remain behind the subsystem capability boundary.

## Encoding policy

The supplied records contain 32-, 64- and 128-bit logical templates as well as fields declared outside the primary word. These remain encoding metadata until a normative wire encoding is frozen.

The emulator ABI remains:

```text
opcode[16] | rd[16] | rs[16] | rt[16] | immediate[64]
```

An assembler/disassembler generator must therefore either normalize each logical template into this packet or introduce an explicitly versioned extension encoding. It must not silently reinterpret the host ABI.

## Source-data conformance observations

The following supplied records require explicit encoding review before they can become normative binary encodings:

1. `ECC_POINT_ADD (0x0043)` contains `rt in separate field`; the location, width and serialization order of `rt` are not fully specified.
2. Several templates for opcodes above `0x00FF` show an 8-bit opcode field while `opcode_bits` is a value such as `0x107`, `0x10A`, or `0x11C`. This cannot be represented by an 8-bit field. The canonical 16-bit opcode identity remains authoritative; the logical encoding must be revised before normative promotion.
3. Some records deliberately place operands in a separate field (for example `SHADER_COMPILE` options and the 0x0043 `rt` field). These are metadata annotations, not a complete binary serialization contract.
4. Example binaries are preserved exactly as supplied. They are golden metadata examples, not a declaration that all field-width arithmetic has already been formally validated.

## Privilege and capability notes

The extension includes privileged operations affecting caches, TLBs, page tables, PCI, DMA, power state, reboot/shutdown, keystores, certificates, security scans and maintenance mode. These must require the normal Chimera II privilege/capability gate and must not execute host-side effects from the pure register core.

User-visible Aurora operations such as presentation, audio, GPU submission and PipeWire integration remain routed through their owning Aurora service boundary.

## Opcode continuity

The extension does not assign values to the omitted range `0x00F0..0x0106`, because no records for that interval were supplied in this change. Existing canonical definitions in `tools/isa/chimera_isa_r8192_complete.csv` remain authoritative for any already-defined instructions in that interval.

## Conformance requirements

Before this extension is promoted to a frozen hardware encoding:

- every opcode must be unique across the complete 284-entry semantic catalog;
- every encoding template must have an unambiguous bit width;
- every operand must have a defined width, position and serialization order;
- opcode width must agree with the numerical opcode range;
- reserved bits must have defined reset/validation behavior;
- example binaries must round-trip through assembler and disassembler;
- privilege and capability checks must be tested;
- service-dispatch tests must distinguish recognized from implemented operations.
