# Chimera II OS

Chimera II OS is a cross-language research operating-system and application platform centered on the Koronos microkernel, wide-register C8192/R8192 research ISA, multidimensional cognition, portable tooling, trusted peer networking and separate Mobile Microkernel/application stacks.

## Complete source-code citation index

| Area | Source |
|---|---|
| Boot / Spit Fire | [boot and firmware trees](.) |
| Jasper boot manager | [boot-manager sources](.) |
| Koronos microkernel | [kernel sources](.) |
| Spotnik networking | [networking sources](.) |
| Application network module | [`network/ApplicationNetworkModule.md`](network/ApplicationNetworkModule.md) |
| Aurora desktop | [`desktop/`](desktop/) |
| Open-source service compatibility | [`services/`](services/) |
| Open-source application catalog | [`applications/`](applications/) |
| Open-source provenance | [`opensource/`](opensource/) |
| RISC/CISC ISA catalog | [`isa/`](isa/) |
| Universal architecture registry | [`isa/world_architectures.json`](isa/world_architectures.json) |
| Universal execution API | [`execution/universal_execution_api.json`](execution/universal_execution_api.json) |
| Retro computer registry | [`emulation/retro_systems.json`](emulation/retro_systems.json) |
| Unix/Linux command registry | [`services/unix_command_registry.json`](services/unix_command_registry.json) |
| Linux package repositories | [`packages/repositories.json`](packages/repositories.json) |
| Aurora application registry | [`desktop/aurora_app_registry.json`](desktop/aurora_app_registry.json) |
| Nucleus / Hive / Kore / Aegis / CEF | [system service trees](.) |
| RegisterN / C8192 / R8192 | [ISA/register sources](.) |
| Quantum computing | [`quantum/`](quantum/) |
| Multidimensional / perspective mathematics | [`multidimensional/`](multidimensional/) |
| Neural reasoning | [`neural/`](neural/) |
| Voice / speech | [`voice/`](voice/) |
| Hardware / GPU / driver registry | [`drivers/`](drivers/) |
| Java hardware/driver + desktop layer | [`java/`](java/) |
| Rust implementation | [`rust/ChimeraIIOS/`](rust/ChimeraIIOS/) |
| Mobile Microkernel | [mobile sources](.) |
| P2P | [protocol sources](.) |
| Automation / ISO / tests | [tools, build and test trees](.) |
| Complete tracked repository | [full source tree](.) |

## Universal ISA, computer and OS registry

`isa/catalog.json` remains the canonical instruction catalog, while `isa/world_architectures.json` is the broader architecture/OS/emulator registry. The normalized instruction model separates architecture, mnemonic, operands, encoding, flags, memory effects, control flow and privilege. The registry is provenance-first: it indexes authoritative specifications and examples rather than copying proprietary manuals. It is designed to drive future assembler/disassembler, emulator, debugger and binary-analysis adapters.

The initial research crawl cross-checks Intel's current Software Developer Manuals, RISC-V specifications, Arm architecture documentation and QEMU's architecture/emulation documentation. Intel's SDM Volume 2 is the authoritative instruction reference for IA-32/Intel 64; RISC-V and Arm publish their own architectural specifications; QEMU provides a practical multi-architecture emulation reference.

## Universal execution API

`execution/universal_execution_api.json` defines the common execution boundary: decoder → operand resolver → semantic engine → machine state → memory bus → device bus → OS/ABI boundary. C/C++, Rust, Python, Java, C#, Kotlin, Swift, TypeScript, Dart and Go adapters can bind to the same model. Privileged execution is sandboxed by default and downloaded code is never executed automatically.

## Aurora Wayland Glass

`desktop/aurora_app_registry.json` makes Aurora the common presentation layer for Settings, Package Center, Terminal, ISA Explorer, CPU Emulator, Retro Center, BizX, BizXtreme, Network Center and Developer Center. The existing event schema and Linux/Windows/macOS compatibility profiles remain the common desktop contract. Wayland is the native Linux compositor boundary; legacy personalities remain behavioral compatibility profiles rather than copied proprietary binaries.

## Retro Computer Center

`emulation/retro_systems.json` establishes a single Aurora registry for Amiga, Commodore, Atari, Apple, Sinclair, Acorn, Amstrad, PC/DOS, arcade and console families. Existing Amiga browser work under `nlp/Amiga` is the first integrated profile. The design uses adapter boundaries for SAE/UAE/vAmigaWeb, QEMU, MAME, libretro and other compatible projects. ROMs, BIOS images and commercial games remain user-supplied or properly licensed.

The libretro ecosystem provides a portable audio/video/input API and a broad collection of emulator cores, while RetroArch acts as a reference frontend. Chimera integrates this ecosystem through adapters rather than copying every emulator into the OS repository.

## Linux / Unix commands and package repositories

`services/unix_command_registry.json` catalogs filesystem, text, process, shell, network, archive, storage, system, development and package utilities. Native Chimera implementations are preferred; compatibility adapters can delegate to a host/Linux environment when appropriate.

`packages/repositories.json` records package repository families including Debian, Ubuntu, Fedora, openSUSE, Arch, Alpine, Gentoo, FreeBSD, Homebrew and Flathub, plus upstream Linux/kernel, GNU, freedesktop, Wayland, Mesa, QEMU and libretro references. Repository metadata does not imply that packages are trusted: Chimera package installation must enforce signatures, checksums, licenses, dependencies, architecture compatibility, permissions and rollback policy.

## BizX and BizXtreme integration

BizX and BizXtreme now contain `CHIMERA_INTEGRATION.json` manifests. Aurora exposes them as applications while Koronos/Chimera APIs provide networking, execution, package, settings, retro and system-service boundaries. Existing language implementations are retained as language-specific adapters; the integration does not claim that one translated codebase replaces all implementations. Each repository's licenses and provenance remain authoritative.

## Cross-repository Chimera integration

Relevant repositories now expose a small `CHIMERA_INTEGRATION.json` contract so the OS can discover their capabilities without copying their entire source trees into the kernel repository. This includes `BizX`, `BizXtreme`, `nlp`, `CPU4096`, `CPU4096Simulator`, `general`, `PDFreaderPY`, `eth-key-check`, `keygen`, `bruteforce`, `test`, `VanG`, and the project website. The integration contract distinguishes reusable application capabilities from repository-specific source and licensing.

## Unified build, dependency, packaging and installer automation

The repository now has a single cross-platform automation entry point: `tools/build/orchestrator.py`, with POSIX shell, Windows CMD and PowerShell wrappers under `scripts/`. Use `doctor`, `deps`, `configure`, `build`, `test`, `package`, `install`, `clean`, or `all`. The same orchestration contract is exercised by CI so local builds and CI builds do not silently diverge.

The build manifest tracks C/C++/ASM, Rust, Python, Node.js/TypeScript, Java, .NET/C#, Kotlin, Swift and Dart toolchains. Dependency installation prefers project manifests/lockfiles and does not execute downloaded scripts. CMake/CTest/CPack provide native configuration, testing and packaging; packages can include portable archives and native OS installers when the host generator is available. GitHub Actions can run matrix builds across Linux, Windows and macOS.

## Arabic-first internationalized desktop

Chimera II now treats Arabic (`ar`, with `ar-SA` as the reference locale) as a first-class desktop language. The Aurora compatibility layer provides an explicit RTL direction, Arabic UI resources, locale contracts in C/C++, Rust, Python, Java, C#, Kotlin, Swift, TypeScript and Dart, and a `Chimera العربية` desktop personality. The Arabic contract covers menus, settings, networking, security, storage, drivers, developer tools, diagnostics, accessibility and system actions.

The desktop compatibility model catalogs GNOME, KDE Plasma, Xfce, Cinnamon, MATE and LXQt on Linux, classic through modern Windows/WinUI, and Classic-Mac/Cocoa/AppKit/SwiftUI-era macOS presentation. These are behavior/appearance compatibility profiles rather than copied proprietary source or binaries. Open-source upstream projects remain subject to their own licenses and provenance requirements.

Arabic UI follows Unicode logical text order and uses platform text shaping/BiDi/layout engines rather than manually reversing strings. RTL tests cover mixed Arabic/Latin text, numerals, paths/URLs, keyboard switching, accessibility, clipping, menus, panels, dialogs and clipboard round trips.

See `desktop/localization/ar-SA.json`, `desktop/upstream_desktop_catalog.json`, `desktop/desktop_profiles.json`, `docs/ARABIC_DESKTOP_AND_LOCALIZATION.md` and `.github/workflows/arabic-desktop-ci.yml`.

## Application networking

`network/ApplicationNetworkModule.md` defines the in-application Network Center for Client, Server, Host (server + local client), P2P and Hybrid modes. Users can choose a nickname and avatar, including a validated local image upload when built-in avatars are unavailable. Spotnik remains the OS networking boundary while application sessions can select QUIC/TLS, TCP/TLS, WebRTC, WebSocket/WebTransport and libp2p adapters.

## Open-source Linux / Windows / macOS services and applications

Chimera II has a provenance-first compatibility layer for open-source services, desktop technologies and free applications. The canonical source registry is `opensource/sources.json`; service capabilities are defined in `services/service_registry.json`; application compatibility records are in `applications/catalog.json`.

The integration covers Linux systemd/D-Bus/NetworkManager/PipeWire/CUPS/udev/Samba families, Windows Service Control Manager/Task Scheduler/PowerShell/Windows Terminal/WSL/Windows App SDK boundaries, and macOS launchd/POSIX/CoreAudio/WebKit/printing boundaries. Aurora remains the common desktop capability layer, while platform adapters preserve each operating system's distinct semantics.

Application families include file managers, terminals, office/document suites, image/PDF tools, media players, browser/WebKit shells, archives, calculators, system monitors, disk/network/developer tools, accessibility, recording, backup/synchronization and package-management interfaces.

These are compatibility and provenance layers rather than a claim that the repository contains every upstream project. Large upstream projects remain external and are represented by versioned source/license metadata and explicit staging/build manifests. Proprietary platform binaries are not redistributed. Downloaded artifacts are not executed automatically.

## Neural multidimensional reasoning

The `neural/` layer combines weighted evidence, disagreement-aware confidence, observer/perspective transforms and multidimensional feature overlays. The intended response pipeline is **evidence → normalization → geometry → observer transform → neural reasoning → confidence → explanation → optional speech**. This makes perspective separate from geometry and keeps uncertainty explicit.

The 128D profile remains an experimental computational semantic representation, not a claim about the number of physical dimensions.

## Voice and speech

`voice/` provides a cross-platform TTS/STT boundary. Providers can target Windows SAPI/WinRT, Linux/Unix Speech Dispatcher/PipeWire/ALSA/PulseAudio, Apple AVFoundation/CoreAudio, or explicitly configured external engines. The core does not silently upload text or audio and does not bundle proprietary speech engines.

## Quantum computing research layer

The `quantum/` tree provides a portable CPU-baseline state-vector simulator, QFT/gate primitives, C ABI, versioned `CHMQ-1` circuit IR, Python/Rust reference implementations and adapters for Java, C#, TypeScript, Kotlin, Swift and Dart. Research integration targets include Qiskit, Cirq, PennyLane, NVIDIA CUDA-Q, cuQuantum and qsim. External quantum services remain opt-in. The implementation is clean-room: upstream projects are architectural and mathematical references, not copied source.

## Hardware, GPU and driver compatibility

The `drivers/` layer contains a stable hardware capability registry covering modern and legacy CPU families, GPU families, PCI/PCIe/USB/virtio/NVMe/SATA/SCSI/I2C/SPI/GPIO/Bluetooth classes, networking, audio, cameras, input and display. It also defines protocol-level printer support including IPP Everywhere, PostScript, PCL5/PCL6, ESC/P, ESC/POS, PDF/PS and a deterministic **Ghost Printer** virtual sink.

Chimera II can discover, acquire, verify and stage Linux and Windows driver candidates through a security-first broker. It never silently loads downloaded code, bypasses Secure Boot/signature enforcement, or treats proprietary driver binaries as redistributable merely because they can be found online.

## Licensing and provenance

Chimera II OS is distributed under GNU GPL v3 or later unless a subcomponent explicitly identifies a compatible third-party license. Third-party dependencies and assets retain their original licenses. The open-source compatibility, emulator and ISA layers record upstream provenance and license expressions instead of assuming that all upstream projects can be relicensed as GPL.
