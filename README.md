# Chimera II OS

**Research-grade modular operating-system, virtual-processor, desktop/mobile, networking, data and intelligent-computing ecosystem.**

> Status: public research/engineering prototype. Host-emulated components are separated from future bare-metal firmware, kernel, driver, FPGA, mobile-hardware and silicon targets.

## Universal ISA and CPU compatibility

Chimera II now uses a layered universal-ISA model. Native C8192/R8192 instructions remain the canonical architecture, while x86-64, AArch64, RISC-V, MIPS64, POWER64, SPARC64, IBM Z/s390x, Motorola 68k, Alpha, PA-RISC, SuperH, Itanium, AVR, Xtensa and WebAssembly are represented as compatibility targets. Foreign instructions are decoded into canonical micro-operations and mapped to `RegisterN<N>` state instead of being flattened into one unsafe opcode namespace.

The ISA registry is in `isa/`, the native/foreign target model is in `include/chimera/universal_isa.hpp`, and the generated/import pipeline is designed around LLVM TableGen-style declarative metadata. LLVM documents TableGen as the mechanism it uses to generate instruction, register, subtarget and searchable target tables. citeturn0search0turn0search2 RISC-V's specification similarly separates a base ISA from standard, reserved and custom extensions, a useful model for Chimera compatibility metadata. citeturn0search9

This is an implementation framework and import pipeline; it does **not** claim that every instruction of every historical CPU has already been manually reimplemented. Imported targets can be native, translated/JITed or emulated depending on hardware capability.

## Database subsystem

Koronos now exposes a userspace database-service boundary for Nucleus/Hive and applications. Supported open-source integration targets include MariaDB Community Server, PostgreSQL, SQLite, DuckDB, RocksDB, LevelDB, Valkey, Apache Cassandra and Apache CouchDB. The repository contains original adapters/manifests rather than copying third-party source trees or binaries.

MariaDB Community Server is GPLv2 and guaranteed open source; PostgreSQL uses the PostgreSQL License; SQLite's deliverable code and documentation are public domain; DuckDB is MIT; RocksDB offers Apache-2.0/GPLv2; Valkey is BSD; and Apache CouchDB is Apache-2.0. citeturn1search2turn1search0turn0search6turn1search1turn1search10turn1search7turn1search6 Exact release/dependency licenses are revalidated before packaging.

Use `database/manifests/open-source-databases.yaml` and `docs/DATABASE_SUBSYSTEM.md` for the integration matrix.

## Koronos microkernel 2

The kernel now has an explicit architecture-context and service registry layer. Wide `RegisterN<8192>` state is lazy, preventing ordinary 64-bit workloads from paying a full wide-register context-switch cost. Database, networking, VFS, virtualization and compatibility execution remain userspace/service boundaries where practical; the kernel handles capabilities, IPC, scheduling, memory and privileged traps.

See `docs/KORONOS_MICROKERNEL_2.md`.

## Existing system architecture

```text
CHIMERA II OS
  |
  +-- Native ISA: R8192 / C8192 / RegisterN / Tensor / Vector
  +-- Compatibility: x86-64 / ARM64 / RISC-V / MIPS / POWER / SPARC / IBM Z / legacy
  +-- Koronos: scheduler / IPC / MM / IRQ / capabilities / VFS / VM / service boundary
  +-- Spit Fire + Jasper: BIOS/UEFI boot and boot manager
  +-- Spotnik: networking
  +-- Nucleus + Hive: HTAP/database/registry layer
  +-- Aurora: graphics/desktop
  +-- CEF: emulation/compatibility framework
  +-- ISO-Tool: source/build/package/ISO orchestration
```

## Unified language matrix

| Language / toolchain | Role | Location |
|---|---|---|
| C / C++ | Kernel, ISA, boot, native desktop and hardware-facing implementation | `src/cpp/`, `src/kernel/`, `src/arch/` |
| Visual C++ / MSVC | Windows-native bootstrap, host integration and installer-facing code | `src/vcpp/` |
| C# | Managed Windows/cross-platform services and desktop tooling | `src/csharp/` |
| F# | Functional .NET research/runtime layer | `src/dotnet/fsharp/` |
| Visual Basic .NET | Managed Windows compatibility/tooling layer | `src/dotnet/vb/` |
| Java | Koronos semantic/JVM interoperability and application-service bridge | `src/java/` |
| Node.js | Web/integration runtime and service bridge | `src/node/` |
| Python | Reference research, ML/RL, data-processing and service bridge | `src/python/` |

## Structured boot and ISO architecture

`boot/spitfire/` contains the staged SF0/SF1/SF2 BIOS implementation sources, SFU UEFI source contract and shared boot ABI headers. `kernel/arch/x86_64/` contains the Koronos boot handoff/linker contract. `boot/iso/build-iso.sh` creates the deterministic ISO 9660/El Torito media tree through GRUB2/xorriso.

The staged tree contains `/boot/spitfire`, `/boot/jasper`, `/boot/koronos`, `/EFI/BOOT`, `/EFI/CHIMERA`, `/chimera`, `/src` and `/checksums`. BIOS Multiboot2 remains the current executable bootstrap; the native Spit Fire stages remain the continuing bare-metal implementation boundary.

## Unified package management

`package-manager/chimera-pkg.py` provides a common command surface while retaining native package managers and provenance-aware repository metadata. The adapter never executes a plan unless `--yes` is explicitly supplied.

## Build and test

```bash
cmake -S . -B build -DCHIMERA_ENABLE_EXPERIMENTAL=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
python3 -m pytest -q tests/isa/test_isa_registry.py tests/database/test_database_catalog.py
cd boot/iso && ./build-iso.sh
```

## Documentation

See `docs/UNIVERSAL_ISA_AND_CPU_ARCHITECTURE.md`, `docs/ISA_DATABASE_RESEARCH.md`, `docs/KORONOS_MICROKERNEL_2.md`, `docs/DATABASE_SUBSYSTEM.md`, `docs/STRUCTURED_ISO_BUILD.md`, `boot/iso/README.md`, `database/docs/DATABASE_BACKENDS.md` and the language-specific READMEs.

The 8192-bit processor remains an architectural/emulation research target, not a claim of existing 8192-bit silicon. Physical performance and energy claims require measured implementations.
