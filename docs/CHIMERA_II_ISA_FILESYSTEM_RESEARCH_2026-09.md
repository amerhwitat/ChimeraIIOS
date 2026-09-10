# Chimera II OS ISA and Universal Filesystem Research — 2026-09

## 1. Scope

This document records the cross-architecture ISA audit and filesystem compatibility expansion approved for Chimera II OS. It is an implementation-oriented synthesis, not a claim that every proprietary architecture instruction or every historical filesystem has been reimplemented in one release.

The design preserves the existing Chimera-II canonical 16-byte instruction packet and existing ABI/opcodes. New functionality is represented as versioned extension classes, semantic operations, compatibility adapters, and conformance tests.

## 2. ISA evidence base

The audit covers the instruction and architectural capability families exposed by contemporary and historical CISC/RISC references:

- x86-64 / IA-32: Intel's current Software Developer's Manuals provide the architecture and the complete A–Z instruction reference, including system-programming material.
- Arm A64: the current 2026-06 A-profile reference exposes base A64 instructions plus SVE/SME families and memory-ordering/atomic instructions.
- RISC-V: the ratified 2026 specification set includes integer multiply/divide, atomics, CSR/system instructions, fences, bit manipulation, vectors, cryptography, compressed/code-size extensions, and floating-point variants.
- IBM POWER: Power ISA 3.1c is organized into user, virtual-environment, and operating-environment books; the current OpenPOWER specification page also identifies approved RFC work for dense math, SHA2/SHA3 and AES facilities.
- IBM z/Architecture: the Principles of Operation separates general, floating-point, control, decimal, vector, I/O, and specialized-function facilities; current IBM documentation also exposes access-register and address-space operations.
- SPARC V9: Oracle's assembler reference documents integer, floating-point, coprocessor, synthetic, VIS, graphics and memory-access instruction families and the V9 changes from V8.
- HP PA-RISC: Linux-on-PA-RISC documentation preserves the PA-RISC 1.1 and 2.0 architecture and instruction-set references. PA-RISC uses fixed-length RISC instructions and includes multimedia/MAX facilities.
- Intel Itanium/IA-64: the Software Developer's Manual family includes a dedicated instruction-set reference, instruction formats, dependency/resource semantics, and IA-32 compatibility behavior.
- MIPS: the MIPS training reference confirms fixed 32-bit instruction words, three-operand forms, register arithmetic, and HI/LO multiply/divide result conventions.

Primary references:

1. Intel 64 and IA-32 Software Developer's Manuals: https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html
2. Arm A64 ISA 2026-06: https://developer.arm.com/documentation/ddi0602/2026-06
3. RISC-V ratified ISA library: https://docs.riscv.org/reference/isa/
4. RISC-V ISA source: https://github.com/riscv/riscv-isa-manual
5. OpenPOWER ISA 3.1c: https://openpowerfoundation.org/specifications/isa/
6. IBM z/Architecture Principles of Operation: https://www.ibm.com/docs/en/systems-hardware/zsystems/3932-A02?topic=library-2
7. SPARC V9 instruction reference: https://docs.oracle.com/cd/E18752_01/html/816-1681/sparcv9-15322.html
8. Linux PA-RISC architecture documentation: https://parisc.docs.kernel.org/en/latest/technical_documentation.html
9. Itanium architecture documentation index: https://www2.lawrence.edu/fast/EVANSJ/Itanium/manuals.html
10. MIPS instruction-set overview: https://training.mips.com/basic_mips/PDF/Instruction_Set.pdf

## 3. Chimera ISA gap model

The audit converts architecture-specific instructions into portable semantic classes rather than copying incompatible encodings. The current Chimera C8192/R8192 model should therefore add or expose these classes:

| Extension | Representative operations | Main source families | Chimera role |
|---|---|---|---|
| BITMANIP | CLZ, CTZ, POPCNT, BEXT, BDEP, bit reverse/rotate | x86, Arm, RISC-V, Power | scalar/vector bit-level acceleration |
| ATOMICS | CAS, SWAP, fetch-add, LL/SC semantic pair | x86, Arm, RISC-V, Power, MIPS | lock-free kernel/runtime primitives |
| MEMORY_ORDER | FENCE, acquire/release, LFENCE/SFENCE semantic forms | x86, Arm, RISC-V, Power | explicit memory-model control |
| VECTOR | VADD, VMUL, VREDUCE, VPERM, gather/scatter | Arm SVE/SME, RISC-V V, Power VSX/VMX, SPARC VIS | scalable 8192-bit lanes |
| MATRIX_TENSOR | MADD, matrix multiply-accumulate, TCONTRACT | Arm SME, Power matrix/dense-math work, Chimera | tensor/HDC/neural workloads |
| CRYPTO | AESENC/AESDEC, SHA2/SHA3, CRC, carry-less multiply | x86, Arm, RISC-V crypto, Power | cryptographic primitives |
| STRING_MEMORY | MOVS, CMPS, REP-style bulk operations, checksums | x86, IBM z, legacy CISC | fast VFS/network/data movement |
| CACHE_MEMORY | PREFETCH, cache line maintenance, memory tagging hints | x86, Arm, RISC-V, Power | latency-aware runtime |
| SYSTEM_CONTROL | syscall, trap, CSR/system-register, TLB invalidation | all major RISC/CISC families | Koronos control plane |
| VIRTUALIZATION | VMRUN, VMEXIT, guest-state operations | x86 VT-x/AMD-V, Arm EL2, RISC-V H, IBM | CEF and virtual machines |
| DECIMAL | packed-decimal/BCD operations and conversions | IBM z, x86 legacy | financial/legacy Unix compatibility |
| PREDICATE | predicate masks, conditional vector execution | Arm SVE/SME, vector ISAs | observer/mask-aware parallelism |
| NETWORK | zero-copy send/receive and queue operations | platform-specific accelerators + Chimera | Spotnik fast path |

The new `isa_extension_catalog.hpp` is intentionally semantic: it does not claim source-ISA encoding identity. Existing Chimera encodings remain unchanged.

## 4. New portable semantic operations

`isa_extension_ops.hpp` supplies portable reference semantics for:

- CLZ, CTZ and POPCNT
- wide vector addition
- wide fused multiply-add semantics over 64-bit lanes
- CRC32C reference semantics
- extension capability discovery

These operations are suitable as compiler lowering targets and as emulator reference behavior. Hardware-specific lowering can replace them without changing the semantic API.

## 5. Encoding and ABI policy

1. Existing canonical Chimera 16-byte instruction packets remain stable.
2. Existing opcode meanings remain stable.
3. New operations are versioned and assigned through the existing opcode-generation pipeline before they become architectural commitments.
4. Architecture-specific instructions are mapped by semantics, not by copying vendor encoding fields.
5. Privileged operations remain separated from user-mode operations.
6. Every new committed operation receives an assembler/disassembler description and at least one conformance test.

## 6. Universal filesystem evidence base

Linux's VFS documentation provides the strongest open implementation model: superblocks, inodes, address spaces, file objects, dentry/path lookup, mount options, network filesystem helpers, and filesystem-specific implementations. The current Linux documentation includes ext2/3/4, Btrfs, F2FS, EROFS, HFS/HFS+, HPFS, NILFS2, NTFS3, NFS, SMB, SquashFS, UDF, VFAT, XFS and many more.

IBM AIX documentation confirms both JFS and JFS2. JFS2 adds larger-file/64-bit capabilities and uses superblocks, allocation maps, allocation groups and B+ trees. AIX also documents CDRFS, UDFS, NFS and other filesystem types.

OpenVMS is different: ODS-2 and ODS-5 are Files-11 structures exposed through OpenVMS/RMS semantics. ODS-5 adds long names, wider character sets, case preservation and deeper directories; current OpenVMS x86-64 releases require ODS-5 system disks. Chimera therefore treats ODS-2/ODS-5 as a semantic compatibility target rather than pretending they are ordinary POSIX filesystems.

The attached Amiga reference establishes the AmigaDOS DOS0/OFS, DOS1/FFS, DOS2/international OFS and DOS3/international FFS identifiers. It also documents Amiga-UNIX partition identifiers for classic System-V and Berkeley-on-System-V formats, and describes CrossDOS handler behavior. These details are now captured in the compatibility matrix and documentation.

Filesystem references:

1. Linux filesystem documentation: https://docs.kernel.org/filesystems/index.html
2. Linux VFS/new-filesystem guidance: https://docs.kernel.org/filesystems/adding-new-filesystems.html
3. Linux JFS: https://docs.kernel.org/6.3/admin-guide/jfs.html
4. Linux System V filesystem: https://docs.kernel.org/6.13/filesystems/sysv-fs.html
5. IBM AIX JFS/JFS2: https://www.ibm.com/docs/en/aix/7.1.0?topic=types-jfs-jfs2
6. IBM JFS2 layout: https://www.ibm.com/docs/en/aix/7.1.0?topic=volumes-jfs2-file-system-layout
7. VSI OpenVMS ODS-2: https://wiki.vmssoftware.com/ODS-2
8. VSI OpenVMS ODS-5: https://wiki.vmssoftware.com/ODS-5
9. VSI OpenVMS extended file specifications: https://docs.vmssoftware.com/vsi-openvms-guide-to-extended-file-specifications/
10. Linux current filesystem index: https://www.kernel.org/doc/html/latest/filesystems/index.html

## 7. Filesystem capability matrix

The implementation classifies formats into four modes:

- **NativeReadWrite** — suitable for direct native VFS integration.
- **NativeReadOnly** — stable native reading where write semantics are unsafe, unsupported or intentionally restricted.
- **UserspaceCompatibility** — adapter/handler layer with explicit foreign semantics.
- **EmulatorOnly** — semantics exposed through an emulator or image tool rather than mounted as a native filesystem.

The matrix currently covers 48 names/families including ext4, XFS, Btrfs, ZFS, JFS/JFS2, UFS, System V, F2FS, NILFS2, EROFS, SquashFS, NTFS3, FAT32, ISO-9660, UDF, Amiga OFS/FFS, CrossDOS, HP-UX VxFS, OpenVMS ODS-2/ODS-5, HFS/HFS+, QNX6, ADFS, AFS, 9P, NFS, SMB3, GFS2, OCFS2, Ceph, OrangeFS, overlayfs, proc/sysfs, tmpfs/ramfs, UBIFS/JFFS2, BFS, Minix, BeFS, ReiserFS, HAMMER2, APFS and Chimera QFS.

The matrix deliberately does **not** assert write support for every format. Foreign formats require dedicated on-disk validation, crash-consistency tests and license review before write support is promoted.

## 8. Compatibility architecture

```text
Chimera applications
        |
 POSIX / Win32 / Unix / VMS RMS / AmigaDOS APIs
        |
   Chimera VFS + Object/Semantics Layer
        |
  +-----+-------------------------------+
  |                                     |
Native filesystem drivers       Foreign compatibility handlers
  |                                     |
Linux/Unix filesystems          Amiga / HP-UX / OpenVMS / legacy
  |                                     |
block/flash/network backends    image adapters / userspace services
```

The semantic layer is the important invariant: a filesystem driver is responsible for on-disk behavior, while the compatibility layer preserves foreign naming, locking, record-management, handler, or volume semantics where POSIX cannot represent them directly.

## 9. Amiga integration

The Amiga reference is incorporated as source material for the compatibility layer. In particular:

- DOS0 identifies the old filesystem/OFS.
- DOS1 identifies FFS.
- DOS2 and DOS3 identify the international variants.
- Amiga-UNIX RDB identifiers include classic System-V and Berkeley-on-System-V filesystem partition types.
- CrossDOS is modeled as a handler-style compatibility filesystem, not as a generic block filesystem.
- Handler packet semantics such as disk serialization and filesystem startup metadata motivate the Chimera foreign-handler interface.

Source: `AmigaGuruBook[ENG]FullSearch(1).txt` supplied with the Chimera II OS work.

## 10. IBM and HP integration

### IBM

JFS is included as a native Unix-family target because Linux already documents an open implementation. JFS2 is represented as an AIX semantic compatibility target because its AIX-specific logical-volume, allocation-group and filesystem-management behavior is broader than the Linux JFS implementation.

IBM z/Architecture's rich decimal, vector, string and address-space facilities inform the ISA semantic catalog, especially DECIMAL, STRING_MEMORY, VECTOR and SYSTEM_CONTROL.

### HP

PA-RISC and Itanium references inform the ISA audit. HP-UX VxFS is represented as a userspace compatibility target rather than a claimed native implementation. This separation avoids conflating HP-UX's filesystem semantics with Linux/Unix VFS semantics.

## 11. Licensing and provenance policy

Chimera II OS does not copy arbitrary Internet source trees into the kernel. Open-source implementations can be reused only under compatible licenses and with their notices preserved. Proprietary documentation is used for interface/semantic research and is not redistributed verbatim. Where licensing or provenance prevents direct code reuse, Chimera implements an independent compatibility layer from documented behavior.

The PA-RISC Linux documentation explicitly warns that many HP documents are copyrighted and should not be redistributed verbatim. This is why the repository records the architectural findings rather than importing HP manuals wholesale.

## 12. Current implementation status

Implemented in this change set:

- cross-architecture ISA extension catalog;
- portable reference operations for bit manipulation, vector arithmetic, multiply-add and CRC32C;
- extension conformance tests;
- 48-entry filesystem capability matrix;
- filesystem matrix conformance tests;
- CMake registration for the new tests;
- this research and provenance document.

Planned next implementation layers remain separate from this metadata layer: per-format image parsers, journal/recovery engines, foreign pathname/record semantics, assembler opcode allocation, full encoder/disassembler generation, compiler intrinsic lowering, and per-architecture emulator backends.
