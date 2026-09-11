# Universal ISA lowering contract

Chimera II OS separates **foreign instruction encoding** from **canonical execution semantics**.

## Pipeline

```text
foreign bytes
    -> architecture decoder
    -> verified instruction descriptor
    -> canonical MicroOp
    -> RegisterN / memory / control state
    -> Koronos execution service
```

The separation prevents historical ISA encodings from being placed into one unsafe global opcode namespace. Native C8192/R8192 instructions retain their canonical identity; x86-64, AArch64, RISC-V, POWER, MIPS, SPARC, IBM Z/s390x and legacy targets are translated, emulated or imported according to the target registry.

## Canonical semantics

`include/chimera/universal_microop.hpp` defines the stable semantic vocabulary for integer, memory, atomic, control-flow, vector, tensor, crypto, I/O, networking, syscall and trap operations. A lowering backend may emit one or more `MicroOpRecord` values for a foreign instruction.

The canonical record has a fixed 16-byte wire representation so emulator and tooling interfaces remain compatible. The immediate field is little-endian in the canonical record; foreign byte order is handled before lowering.

## RegisterN integration

The semantic layer is width-independent. Register operands address the active architectural register file, allowing a translated 32/64-bit instruction to operate on an appropriately sized view while native Chimera execution can use `RegisterN<8192>` and future wider configurations. Backends must explicitly define truncation, extension, flags and exception behavior rather than silently changing state width.

## Privilege and faults

A lowering contract identifies whether an operation is privileged, can trap, or accesses memory. Koronos remains responsible for capability checks, address-space protection, scheduling, IPC and privileged traps. Device, network and filesystem operations remain service boundaries where practical.

## Coverage policy

The target registry is a compatibility manifest, not a claim that every historical processor instruction has been manually reimplemented. Exact encodings should only be added when verified against authoritative architecture documentation or a compatible open-source decoder. Otherwise the implementation records the semantic mapping boundary and routes execution through an emulator/JIT/import backend.
