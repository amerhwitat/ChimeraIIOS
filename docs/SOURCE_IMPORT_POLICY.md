# Chimera II OS Source Import and Clean-Room Policy

## Purpose

Chimera II OS may learn from, interface with, and selectively incorporate source code that is legally redistributable under compatible licenses. The project does **not** ingest or redistribute unlawfully disclosed, leaked, stolen, confidential, or trade-secret source.

## Linux and open-source systems

Linux kernel code is GPL-2.0-only with an explicit Linux syscall exception; individual files can carry compatible licenses and must retain their SPDX notices. Chimera II therefore uses Linux as a compatibility/reference source and imports only specifically reviewed files whose licenses permit redistribution. See the Linux kernel licensing documentation and `library/provenance/INDEX.md`.

For distribution-wide functionality, Chimera uses an adapter model rather than copying every distro's complete source tree. Distro-specific packages, patches, init systems, utilities, drivers, and configuration are tracked as external upstreams with version/license metadata. Equivalent clean implementations are preferred for the Chimera kernel and Mobile Microkernel.

## Windows source

Microsoft states that illegally disclosed Windows NT 4.0/Windows 2000 source is copyrighted and protected as a trade secret and that downloading, posting, or sharing that material is illegal. Chimera II therefore does **not** copy, port, or redistribute leaked Windows source from the Library or Internet.

Windows compatibility is implemented from public documentation, published interface specifications, legally redistributable SDK/WDK material, observed behavior, and clean-room code. Proprietary Microsoft implementation details remain outside the repository.

## Architecture strategy

1. Keep native Chimera implementations independent from foreign kernel source trees.
2. Use stable POSIX, ELF, PE/COFF, Win32-compatible, Linux-compatible, and driver interfaces where legally documented.
3. Preserve SPDX/license and provenance metadata for every imported source component.
4. Never treat a reference implementation as evidence of hardware support.
5. Prefer generated interface metadata and conformance tests over source-tree copying.
6. Apply the same rules to the Mobile Microkernel.

## ISA provenance

`tools/isa/isa_opcodes.csv` contains the canonical Chimera R8192/C8192 instruction catalog. Foreign ISA instructions are represented through architecture adapters and translation metadata rather than being falsely claimed as native Chimera opcodes. LLVM documents a broad set of supported target architectures and provides a model for retargetable backends.

## Status labels

- `native`: implemented as Chimera architecture behavior
- `emulated`: executed by a software compatibility layer
- `adapter`: maps a foreign ABI/ISA to Chimera services
- `reference`: informational upstream material
- `planned`: design target not yet implemented

No leaked or confidential source is a valid `native`, `emulated`, or `adapter` implementation input.
