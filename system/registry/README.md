# Koronos CHMRG01 registry hives

CHMRG01 is an open, versioned hierarchical binary registry inspired by the operational model of Windows registry hives. It is **not** Microsoft's SAM file format and does not parse SAM databases.

Hives: machine (identity/detection policy), environment (process defaults), kernel (bounded diagnostics/scheduler preferences). 40-byte little-endian header: magic `CHMRG01\\0`, major/minor, header size, total size, entry count, generation, payload CRC-32 and header CRC-32. Header CRC covers bytes 0..35; payload CRC covers all records. Each record contains path length u16, type u8, flags u8, value length u32, canonical lowercase UTF-8 path and raw value. Types are u32/u64/bool/string/bytes. Duplicate paths, unknown versions/types, invalid lengths, bad CRCs and trailing bytes are rejected.

Build/verify: `python3 tools/registry/registry_hive.py build --input system/registry/machine.defaults.json --output build/registry/machine.hive`; then `verify build/registry/machine.hive`. Kernel parser exposes read-only views only. VFS ownership and authorization are mandatory for writes; use temporary-file + fsync + atomic rename and increment generation per commit.

Security boundary: editable hives cannot enable unsupported CPU features, alter syscall numbers, bypass privilege checks, widen detected physical-address limits or claim CPUs online. Hardware/firmware probes and compiled Kconfig remain authoritative. A full VFS-backed registry service, authenticated writes and crash-recovery acceptance remain pending.
