# Cross-platform command and ISA provider matrix

## Source-of-truth files

| Concern | Catalogue / policy |
|---|---|
| Online command names and source references | `system/commands/online-command-catalog.json` |
| Windows / cross-platform command reference index | `system/commands/ss64-command-catalog.json` |
| Runtime command capability evidence | `system/commands/command-runtime-capabilities.json` |
| Linux command provider inventory | `config/linux-command-registry.json` |
| Provider selection and binary staging policy | `system/commands/compatibility-binary-policy.json` |
| POSIX, Linux, BSD, Darwin, Solaris and shell families | `tools/shell/chimera_command_sources.json` |
| ISA encoding catalogue | `isa/catalog.json` |
| ISA instruction database | `isa/isa_database.json` |
| Command / ISA coverage and evidence counts | `system/commands/command-isa-coverage.json` |

The current coverage record reports 853 unique command names, 104 catalogued ISA architectures, and 15 commands implemented in the native multicall source. These are inventory counts, not proof that all commands or ISA backends are implemented.

## Command provider resolution

A command name is a portable request, not a promise that the same executable, options, output, or side effects exist on every platform. Resolve each request using this order:

1. Chimera-native implementation, if the command has a tested native implementation.
2. Native provider already present in the selected target root filesystem.
3. An official, license-compatible package provider selected for that OS and CPU target.
4. A compatibility adapter only when its semantics are explicitly covered by tests.
5. Otherwise report `provider-missing`; never create a placeholder executable or infer support from catalogue presence.

| Platform | Native command families / providers | Executable and CPU mapping |
|---|---|---|
| Linux | POSIX utilities, GNU Coreutils, BusyBox, util-linux, systemd/Kore frontends, Bash/dash/Zsh | ELF; x86_64, AArch64 and RISC-V64 are the current native command cross-build targets |
| Windows | CMD built-ins, PowerShell cmdlets, Windows system utilities and documented Win32/NT APIs | PE/COFF; x86_64 and ARM64 require target-specific providers; PowerShell is also available cross-platform |
| macOS | Darwin/BSD userland, POSIX utilities, zsh, Apple Command Line Tools | Mach-O; x86_64 and arm64; do not redistribute Apple's proprietary binaries |
| FreeBSD / other BSD | BSD userland, sh/csh/tcsh/ksh and package-provided utilities | ELF on supported BSD targets; provider and ABI must be validated for the exact release |
| Solaris / illumos | System V-derived utilities, ksh/sh and platform packages | ELF; architecture/provider status must be independently validated |

Linux, Windows and macOS commands that share a name can differ in flags and behavior. The command registry must retain provider identity, platform, package/source, license, option schema and runtime-test result. SS64 is a reference index only; it is not a binary or source provider.

## ISA-to-CPU mapping

The ISA catalogue is architecture metadata. It is not an executable backend. For each ISA family, a build artifact must be associated with:

- exact architecture / subarchitecture and ABI;
- object format and machine identifier (ELF, PE/COFF or Mach-O);
- endianness, word size, ABI and required extensions;
- compiler, assembler, linker and disassembler versions;
- instruction-form coverage and operand validation;
- emulator/JIT backend or physical CPU availability;
- build hash and native/emulated runtime evidence.

The current command matrix cross-compiles the real native multicall implementation for Linux x86_64, AArch64 and RISC-V64. Cross-compilation and ELF-header inspection do not establish execution on those CPUs. Other ISA families remain catalogued until a genuine toolchain or validated emulator is built and tested.

## Binary compatibility and licensing

Binary inspection identifies headers and machine types; it does not itself make foreign binaries executable. Linux ELF, Windows PE/COFF and macOS Mach-O require distinct loaders, ABIs, system-call surfaces and libraries. Compatibility mode must use an explicit provider/runtime such as a validated emulator or ABI layer and must fail closed for unsupported instructions or imports.

Only redistributable open-source binaries may be staged. Windows and macOS proprietary operating-system binaries are not copied into Chimera or OctavianOS. Official provider packages must retain upstream source, version, license, checksum and architecture metadata.

## Release evidence

A command or ISA entry is production-ready only after its target-specific artifact is built, inspected, installed into a test rootfs, invoked with representative options/operands, and passed runtime tests. The catalogue must distinguish at least `catalog-only`, `provider-missing`, `cross-compiled`, `runtime-tested`, and `production-integrated`.
