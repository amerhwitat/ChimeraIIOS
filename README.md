# Chimera II OS

Chimera II OS is a cross-language research operating-system and application platform centered on the Koronos microkernel, wide-register C8192/R8192 research ISA, multidimensional cognition, portable tooling, trusted peer networking and separate hosted/bare-metal computer and mobile editions.

## Editions

Chimera II is split into two installation models while retaining shared APIs and services:

- **Hosted Edition** — runs on top of an existing Windows, Linux/Unix, macOS, Android or iOS/iPadOS operating system as an application/runtime environment.
- **BareMetal Edition** — boots directly on supported computer or mobile hardware through a validated boot path and hardware adaptation layer.

See `editions/` and `editions/mobile/mobile_editions.json`.

### Mobile editions

Android has both an APK/AAB hosted edition and a device-profiled bare-metal edition. Android is a Linux-based stack with a HAL and ART, so the hosted edition uses Android application/native boundaries instead of attempting kernel replacement from an ordinary app. citeturn0search0turn0search1

Android bare-metal work uses AArch64/device profiles and can integrate with GKI/KMI, vendor modules, AVB, device-tree, A/B or dynamic partitions where the hardware supports them. Android documents GKI as a generic kernel with a stable KMI and vendor modules, while GSI installation is limited to qualifying devices and requires an unlocked bootloader and Treble compliance. citeturn0search4turn0search2

Apple mobile has a hosted Swift/Objective-C/C++ edition for iOS/iPadOS. Apple platform security uses a cryptographically verified secure-boot chain beginning at immutable Boot ROM, so Chimera does **not** claim universal bare-metal flashing of stock locked iPhones/iPads. Bare-metal Apple targets are research/device-profile targets only where a lawful and technically available alternative boot path and sufficient hardware interfaces exist. citeturn0search47

`mobile/device_matrix.json` records manufacturer/model/SoC/ISA/GPU/display/storage/boot/security/driver capabilities. It covers Android device families, iPhone/iPad generations and additional mobile operating-system families through capability-based adapters rather than claiming that one image boots every phone.

## Universal ISA, operands and binary encodings

The ISA layer is now split into a family index and a canonical instruction database:

- [`isa/world_architectures.json`](isa/world_architectures.json) — enumerates Chimera-native, RISC, CISC and EPIC families, their word widths, encoding models and instruction-form coverage.
- [`isa/isa_database.json`](isa/isa_database.json) — normalized machine-readable ISA database. Each instruction row contains architecture, mnemonic, form, operand kinds, assembly syntax, instruction width, canonical binary value and binary fixed-bit mask.
- [`isa/instructions.json`](isa/instructions.json) — export contract pointing to the canonical database so duplicated instruction data cannot drift.
- [`isa/isa_database.sql`](isa/isa_database.sql) — SQLite schema with architecture, source and instruction tables plus indexes/views.
- [`tools/validate_isa_registry.py`](tools/validate_isa_registry.py) — checks cross-file architecture references, duplicate forms and binary-width validity.
- [`tools/load_isa_database.py`](tools/load_isa_database.py) — loads the canonical JSON into SQLite.
- [`tools/isa_registry_report.py`](tools/isa_registry_report.py) — reports ISA family and instruction-form coverage.

The current registry enumerates x86/x86-64, AArch64/A32, RISC-V, MIPS, Power ISA, SPARC V9, Motorola 68000, IBM z/Architecture, VAX, SuperH, LoongArch, Alpha, PA-RISC, Xtensa, AVR, MCS-51/8051, Z80, 6502, Itanium/IA-64, and Chimera C8192/R8192. The instruction database contains canonical forms for core arithmetic, logical, load/store, branch/call/return, system and native Chimera operations; it uses `value_bits` plus `mask_bits` because parameterized instructions do not have one universal binary value. Official ISA specifications remain authoritative for complete architecture-specific opcode matrices.

### Chimera-native instruction namespace

The project-defined C8192 registry includes `ADD`, `MUL`, `TCONTRACT`, `MODEXP` and `NETSEND` forms. Their binary selectors are **Chimera II project encodings**, not claims about an external commercial ISA. R8192 shares the architecture family and can receive a separately qualified encoding map as the native execution layer evolves.

## Aurora Wayland Glass — world language desktop

Aurora defines a Unicode/CLDR/BCP-47 language and writing-system boundary for the desktop and mobile presentation layers. It supports dynamic language/locale discovery, Unicode BiDi, LTR/RTL/mixed-direction layouts, script-aware shaping/font fallback, multilingual keyboards, IMEs and localized dates, numbers, currencies, units, collation and plural rules.

## Complete source-code citation index

| Area | Source |
|---|---|
| Editions | [`editions/`](editions/) |
| Mobile editions | [`editions/mobile/`](editions/mobile/) |
| Mobile device matrix | [`mobile/device_matrix.json`](mobile/device_matrix.json) |
| Mobile Hardware Adaptation Layer | [`hal/mobile/MHAL.md`](hal/mobile/MHAL.md) |
| Mobile Microkernel | [mobile sources](mobile/) |
| Boot / Spit Fire | [boot and firmware trees](boot/) |
| Jasper boot manager | [boot-manager sources](boot/) |
| Koronos microkernel | [kernel sources](kernel/) |
| Spotnik networking | [networking sources](network/) |
| Aurora desktop | [`desktop/`](desktop/) |
| Aurora localization | [`desktop/localization/`](desktop/localization/) |
| Hardware / GPU / driver registry | [`drivers/`](drivers/) |
| Universal ISA family registry | [`isa/world_architectures.json`](isa/world_architectures.json) |
| ISA instruction database | [`isa/isa_database.json`](isa/isa_database.json) |
| ISA SQLite schema | [`isa/isa_database.sql`](isa/isa_database.sql) |
| ISA validator / loader / report | [`tools/validate_isa_registry.py`](tools/validate_isa_registry.py) |
| Universal execution API | [`execution/universal_execution_api.json`](execution/universal_execution_api.json) |
| Retro Computer Center | [`emulation/retro_systems.json`](emulation/retro_systems.json) |
| Unix/Linux command registry | [`services/unix_command_registry.json`](services/unix_command_registry.json) |
| Package repositories | [`packages/repositories.json`](packages/repositories.json) |
| Nucleus / Hive / Kore / Aegis / CEF | [system service trees](.) |
| Quantum computing | [`quantum/`](quantum/) |
| Multidimensional mathematics | [`multidimensional/`](multidimensional/) |
| Neural reasoning | [`neural/`](neural/) |
| Voice / speech | [`voice/`](voice/) |
| Rust implementation | [`rust/ChimeraIIOS/`](rust/ChimeraIIOS/) |
| Automation / ISO / tests | [tools, build and test trees](.) |

## Universal ISA and execution

`isa/world_architectures.json` is the broader architecture/OS/emulator registry. `execution/universal_execution_api.json` defines decoder → operand resolver → semantic engine → machine state → memory bus → device bus → OS/ABI boundaries across Chimera and supported architectures.

## Networking and applications

Spotnik remains the OS networking boundary. Application sessions support Client, Server, Host, P2P and Hybrid modes through the documented networking adapters. BizX and BizXtreme expose `CHIMERA_INTEGRATION.json` contracts and can appear through Aurora.

## Security and provenance

Downloaded code, drivers, firmware, ROMs and applications are never automatically executed or loaded. Installation requires compatibility validation, signed-image verification where applicable, explicit partition selection, recovery/rollback planning and device-specific qualification. Third-party licenses remain authoritative.
