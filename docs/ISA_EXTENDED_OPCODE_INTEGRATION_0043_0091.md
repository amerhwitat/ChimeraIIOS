# Chimera II ISA — Extended Opcode Integration 0x0043–0x0091

**Status:** Integrated metadata layer
**Architecture:** R8192 / Chimera II
**Repository:** `amerhwitat/ChimeraIIOS`

## Purpose

This document records the extended ISA records supplied for integration into the Chimera II machine-readable ISA metadata. The records extend the encoding metadata for cryptography, system/control, memory, Spotnik I/O/networking, VFS, NDB/Hive, and Aurora GPU/media interfaces.

The integration preserves existing semantic opcode identity. The supplied encoding templates and example binaries remain **illustrative metadata**, not a declaration of final silicon encoding.

## Integrated records

| Range | Domain | ISA family | Records |
|---|---|---|---:|
| `0x0043–0x0044` | ECC | R8192 | 2 |
| `0x0045–0x0068` | System/control/task/memory | HYBRID | 36 |
| `0x0069–0x006F` | DMA/network/I/O | SPOTNIK | 7 |
| `0x0070–0x0084` | Filesystem/VFS | VFS | 21 |
| `0x0085–0x008B` | Database/registry | NDB/HIVE | 7 |
| `0x008C–0x0091` | GPU/Aurora | AURORA | 6 |

The machine-readable source is:

`tools/isa/isa_opcodes_expanded_with_encodings.csv`

## Architectural interpretation

The extended operations are dispatched through the existing Chimera II execution pipeline:

`FETCH → LENGTH/OPCODE CHECK → DECODE → PRIVILEGE + CAPABILITY CHECK → SUBSYSTEM DISPATCH → RETIRE`

The following subsystem boundaries are retained:

- **R8192:** ECC arithmetic and wide cryptographic primitives.
- **HYBRID:** traps, system calls, interrupt controls, cache/trace/debug controls, tasking, synchronization, and kernel memory helpers.
- **SPOTNIK:** pinned pages, frame mapping/reclamation, event notification, and network backend operations.
- **VFS:** file and filesystem operations.
- **NDB/HIVE:** persistent database and registry operations.
- **AURORA:** GPU, EGL, DMA-BUF, and presentation/media operations.

## Privilege model

`priv` instructions must be mediated by the kernel/security capability layer. The pure R8192 register execution core must not convert these metadata records into unrestricted host-side effects.

`user` instructions may still require object handles, address validation, capability checks, memory-domain validation, or subsystem-specific policy before execution.

## Encoding-width policy

The metadata contains 32-, 48-, 64-, and 128-bit illustrative layouts. This does **not** replace the current canonical emulator instruction container. Variable-width encoding is treated as an ISA/toolchain specification until a formally approved hardware encoding ABI is established.

Where an example binary or field allocation is internally inconsistent, the record is retained as supplied and must be reported by conformance tooling rather than silently rewritten.

## Source completeness

Two boundaries were intentionally not invented:

1. The source preceding `ECC_POINT_ADD` begins with an incomplete record containing only `operation;internal;...`; no mnemonic or opcode identity was supplied, so no artificial instruction was created for it.
2. The supplied text ends during the `PIPEWIRE_PUBLISH` record at opcode `0x0092`; that incomplete record is not included until its complete row is supplied.

This preserves provenance and prevents accidental opcode assignment.

## Conformance requirements

Future assembler/disassembler/emulator tooling should validate:

- mnemonic/opcode agreement with the semantic ISA registry;
- opcode uniqueness;
- legal privilege classes;
- legal ISA-family names;
- encoding field widths and total width;
- immediate-size compatibility;
- `modrm_like` syntax;
- example-binary hexadecimal validity;
- reserved-bit expectations;
- consistency between encoding templates and examples;
- subsystem dispatch availability.

A recognized opcode is not by itself evidence that the underlying subsystem is fully implemented.
