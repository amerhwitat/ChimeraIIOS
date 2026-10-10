## Java portfolio migration

The initial cross-repository Java audit, parity rules, and phased conversion plan are tracked in [docs/JAVA_PORTFOLIO_MIGRATION.md](docs/JAVA_PORTFOLIO_MIGRATION.md). The migration preserves freestanding boot/kernel boundaries and does not claim untested ports are complete.

# Chimera II OS

Chimera II OS is a cross-language research operating-system and application platform centered on the Koronos microkernel, wide-register C8192/R8192 research ISA, multidimensional cognition, portable tooling, trusted peer networking and separate hosted/bare-metal computer and mobile editions.

## Hosted Edition (64-bit Windows / Linux / Unix / macOS)

The portable user-mode bridge is `tools/runtime/chimera-hosted.py` and installs as `chimera-hosted`. It reports host OS/CPU details, matches the detected physical ISA to the canonical ISA inventory, provides a limited set of cross-platform command aliases and opens files/URLs through the host desktop. It does not replace the host kernel or claim complete Windows API, Linux syscall, BSD, or Darwin compatibility.

```sh
chimera-hosted info
chimera-hosted compat list
chimera-hosted isa
chimera-hosted desktop-info
chimera-hosted open .
```

See [Hosted Edition design, compatibility boundaries and limitations](docs/hosted-edition.md) and the machine-readable [compatibility matrix](system/hosted/compatibility-matrix.json). Windows PE validation is distinct from actual binary execution; cross-ISA candidates are not executable without a validated backend. The requested `win-asm.txt` source file was not present in the repository or found in the available file search, so its exact code still needs to be supplied before it can be faithfully integrated.

## Editions

- **Hosted Edition** — runs on Windows, Linux/Unix, macOS, Android or iOS/iPadOS as an application/runtime environment.
- **BareMetal Edition** — boots directly on a validated computer/mobile hardware profile through BIOS/MBR, UEFI or a platform-specific mobile boot path.

## Native C / C++ / ASM and N-bit toolchain

Chimera II OS now includes a source-first native toolchain under `tools/chimera-toolchain/` and the reusable arbitrary-width integer runtime under `lib/chimera-nbit/`. The toolchain is designed around the same separation used by LLVM: logical arbitrary-precision values are represented independently from physical target instruction selection. LLVM's `APInt` explicitly supports non-byte-width and values larger than 64 bits, making it an appropriate reference implementation pattern for Chimera's N-bit layer. citeturn0search1turn0search15

The native target registry covers x86/i386/x86-64, ARM/AArch64, RISC-V 32/64, MIPS64, PowerPC64LE, s390x and WebAssembly 32/64, plus an explicitly experimental `chimera8192` backend contract. LLVM's RISC-V target documentation confirms target-specific code generation and extension handling, while QEMU documents broad guest coverage including x86, Arm, RISC-V and other architectures. citeturn0search17turn0search3

`tools/chimera-toolchain/chimera-ncc` accepts `--chimera-bits=N` or `CHIMERA_BITS=N`. This defines the logical arithmetic width; it does **not** falsely claim that an ordinary CPU has an N-bit physical register. Wide values are lowered into the selected physical target's machine-word operations or handled by the runtime. A true Chimera machine-code backend remains a separate experimental compiler-backend track.

Examples:

```sh
CHIMERA_BITS=8192 tools/chimera-toolchain/chimera-ncc -std=c17 -O2 -c kernel.c -o kernel.o
CHIMERA_BITS=16384 tools/chimera-toolchain/chimera-ncc -x=c++ -std=c++20 -O2 -c app.cpp -o app.o
```

GCC's documented backend model remains the reference for adding a real physical Chimera target: a target backend supplies machine descriptions, target headers/source, options and related configuration. citeturn0search14

The architecture manifest is `tools/chimera-toolchain/architectures.json`; CMake integration is provided by `tools/chimera-toolchain/CMakeLists.txt`. The existing `tools/chimera-asm/` assembler/disassembler remains the Chimera-Bit assembly boundary.

## Universal boot and startup

The boot layer uses a normalized `CHMBOOT1` contract in `boot/boot_protocol.json`. Computer boot targets include BIOS/MBR, UEFI, Multiboot1/2, Limine-compatible handoff and controlled chainloading. BIOS legacy services and modern UEFI protocols/services are treated as separate firmware interfaces.

On x86/x86-64, the mode-transition boundary is real16 -> protected32 -> long64. Other architectures use their native privilege/exception levels rather than pretending they have x86 real mode.

Startup is **menu first, GUI second**. Jasper/Spit Fire exposes Live, Install, Safe Graphics, Diagnostics, Recovery, Network Install/Recovery and controlled native-chainload choices. After handoff, Aurora presents the **Gates Menu** for desktop personalities, applications, games, networking, crypto/wallet tools, Thamudic, NLP, browsers, development and system administration.

The boot visual is represented by `boot/splash/aurora_boot_splash.svg`; the requested support footer is stored in `boot/splash/support_footer.txt` and staged into the ISO.

## Universal source-first ISO

The structured ISO builder stages `/src`, `/opt`, `/install`, `/drivers`, `/filesystems`, `/packages`, `/repositories`, `/man`, `/games`, `/wallets` and `/ISO` as documented distribution contracts.

The first release target is x86-64 with BIOS/MBR and UEFI/GPT qualification. El Torito optical boot and UEFI removable-media structures are authored through GRUB/xorriso.

## Installer and compatibility contracts

`install/installer-contract.json` defines the transaction stages for hardware detection, partition planning, filesystem planning, IPv4/IPv6 configuration, driver/package planning, explicit confirmation, verification and boot-entry registration.

The registries separately describe filesystem capabilities, drivers, binary formats and package managers. A registry entry is not a claim that every target supports every operation.

Windows/Linux/macOS migration is designed as discovery/import/migration rather than silent replacement. Secure Boot, vendor recovery, Android Verified Boot and Apple security mechanisms are not bypassed.

## Application integrations

`appcenter/catalog/external-integrations.json` defines source-first integrations for public repositories including `amerhwitat/nlp`, `amerhwitat/BizX`, `amerhwitat/BizXtreme` and `amerhwitat/general`. Applications are built only when their source, license, dependencies and target compatibility can be verified. Proprietary binaries and drivers are not copied merely because they are discoverable online.

## Mobile editions

Android has hosted APK/AAB and device-profiled bare-metal paths. iOS/iPadOS packaging remains separate from the computer microkernel implementation and is subject to platform security and signing requirements. Flash/recovery helpers are device-profile constrained and confirmation-gated.

## CI and releases

`.github/workflows/chimera-iso.yml` validates registries, boot assets, ISO contents, El Torito/system-area metadata and BIOS/UEFI QEMU smoke paths where firmware is available. `.github/workflows/chimera-release.yml` publishes a GitHub Release only for version tags after the ISO build and verification succeed.

## Security and provenance

Downloaded code, drivers, firmware, ROMs and applications are not automatically trusted. Secure Boot, Android AVB, vendor boot protections and Apple secure boot are respected. Bare-metal automation does not silently flash hardware or erase disks; target selection, compatibility validation, signature/hash verification and recovery/rollback remain explicit.

## Native QFS storage and hardware-learning driver recommendations

Chimera II OS declares **QFS** as its native block filesystem. The default allocation block is **4 KiB**, with explicit installer choices of 8, 16, 32, or 64 KiB. Native installation rejects a block size larger than the running kernel page size.

## 2026 Aurora platform enhancements

Aurora now tracks a capability-detected modern Wayland baseline including fractional
scaling, color management/HDR, tearing control, VRR-oriented low-latency behavior,
GPU-accelerated remote desktop, OCR, reduced-motion accessibility and per-screen
virtual desktops. These are exposed as capabilities rather than unconditional
claims, so unsupported hardware or compositors fall back safely.

The security baseline now includes optional Landlock filesystem/network/IPC
sandboxing profiles, while the boot roadmap includes sealed UKIs, Secure Boot,
composefs/fs-verity integrity and automatic rollback. Virtualization profiles
track current QEMU capabilities including virtio-GPU multi-output and confidential
VM support. MAME integration tracks current controller, latency, netplay, rewind
and runahead capabilities where the selected emulator/core supports them.

See `docs/CHIMERA_AURORA_2026_ENHANCEMENT_RESEARCH.md` and
`system/security/aurora-landlock-profiles.json`.

## Aurora Wayland Glass desktop and menu background

The Aurora Wayland Glass artwork is the canonical Chimera II OS visual background for GRUB, Jasper, Spit Fire, installation/recovery/diagnostics menus, Aurora Gates and the runtime desktop.

## Resumable ISO builds

`build-chimera-iso.sh` retains checkpoints and failure metadata so expensive Docker/rootfs/boot/branding/SquashFS/ISO stages can resume without intentionally discarding completed work.

## RegisterN and Chimera Bit Mode

RegisterN removes the fixed 8192-bit architectural ceiling. Register width is runtime-selected and stored as 64-bit limbs, allowing 8192-bit, 16384-bit, 32768-bit, 65536-bit and larger logical registers without changing the ISA interface. Logical Chimera cores/threads execute in parallel over detected physical CPU cores and hardware threads. x86-64 CISC, ARM64 and RISC-V hosts are treated as physical execution backends through a canonical Chimera micro-op boundary.

## Native assembler, disassembler and reverse engineering

`tools/chimera-asm/` defines the CHIMERA-BIT instruction contract and provides native assembler/disassembler prototypes. The format is width-neutral and carries machine metadata, symbols, relocations and reverse-engineering information for control-flow and register analysis.

## ER/MDM + OLTP/OLAP/HTAP data platform

`system/database/` defines a Nucleus-facing enterprise data architecture combining ER modeling, master-data management, OLTP, OLAP and HTAP.

## Apache ecosystem integration

`services/apache/apache-projects.json` is the source-first integration catalog for Apache ecosystem families. Apache components remain optional userland services and are never linked into the freestanding Koronos kernel.

## PHP / HTML / CSS / JavaScript

`web/runtime/` provides the web-runtime contract and example application assets. PHP is isolated behind a FastCGI-compatible process boundary; HTML/CSS are static web assets; JavaScript executes in a sandboxed runtime.

## Mobile edition and flash tool

The mobile edition shares the same source-first contracts through `mobile/mobile-sync.json`. Android packaging targets hosted APK/AAB delivery and device-profiled recovery integration; iOS/iPadOS remains an Apple-hosted target using Xcode and platform signing. The native C/C++/ASM toolchain contracts are reused rather than forked.

`tools/flash/chimera-flash` provides detection, manifest validation and a confirmation-gated Android flashing boundary. It intentionally refuses generic partition writes until a validated device profile supplies exact partitions, image hashes/signatures, AVB and rollback metadata.


## Aurora PlayStation Emulator Hub

Aurora now includes a unified PlayStation emulator catalog covering PSX/PS1, PS2, PS3, PS4 and PS5. The hub uses capability detection and native adapters rather than pretending that every emulator is bundled or compatible with every machine. Current integrations include DuckStation/Mednafen/Beetle PSX/PCSX ReARMed/SwanStation for PSX, PCSX2 and Play! for PS2, RPCS3 for PS3, shadPS4/RPCSX/fpPS4 for PS4, and KytyPS5/RPCSX for PS5.

The catalog and UI are web/playstation_emulators.json, web/playstation_emulators.html, web/playstation_emulators.js, and web/playstation_emulators.css. The native adapter is tools/emulation/playstation-launcher.sh. Aurora intentionally does not redistribute games, BIOS, encryption keys, or proprietary PlayStation firmware; those remain user-supplied and subject to applicable rights. PS4/PS5 entries are explicitly marked experimental where appropriate.

## Native malware, spyware and firewall protection

The native security stack under `tools/security/` provides layered SHA-256, heuristic, optional ClamAV/YARA and local RNN scoring, with quarantine support and atomic, hash-verified security-intelligence updates. A six-hour systemd timer provides the regular update cadence; model artifacts are treated as data and cannot replace the scanner or policy. The firewall controller uses nftables with private, public, wide-area and domain profiles, default-deny inbound/forwarding policy, and established-connection handling. CI compiles the security modules, runs EICAR regression tests, validates manifests, and checks nftables syntax.


## 32-bit Hosted Edition

The user-space Hosted Edition defines a 32-bit profile for compatible x86 Windows, Linux and BSD/POSIX hosts, alongside 64-bit hosts. It requires a matching 32-bit Python runtime and compatible native dependencies. This does not mean the 64-bit Koronos kernel, 64-bit binaries, drivers or cross-bitness libraries run on 32-bit systems. See [the hosted-edition guide](docs/hosted-edition.md) and [compatibility matrix](system/hosted/compatibility-matrix.json). Current macOS support remains 64-bit only.
