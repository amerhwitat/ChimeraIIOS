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

## Unified build, dependency, packaging and installer automation

The repository now has a single cross-platform automation entry point: `tools/build/orchestrator.py`, with POSIX shell, Windows CMD and PowerShell wrappers under `scripts/`. Use `doctor`, `deps`, `configure`, `build`, `test`, `package`, `install`, `clean`, or `all`. The same orchestration contract is exercised by CI so local builds and CI builds do not silently diverge.

The build manifest tracks C/C++/ASM, Rust, Python, Node.js/TypeScript, Java, .NET/C#, Kotlin, Swift and Dart toolchains. Dependency installation prefers project manifests/lockfiles and does not execute downloaded scripts. CMake/CTest/CPack provide native configuration, testing and packaging; packages can include portable archives and native OS installers when the host generator is available. GitHub Actions can run matrix builds across Linux, Windows and macOS.

## Arabic-first internationalized desktop

Chimera II now treats Arabic (`ar`, with `ar-SA` as the reference locale) as a first-class desktop language. The Aurora compatibility layer provides an explicit RTL direction, Arabic UI resources, locale contracts in C/C++, Rust, Python, Java, C#, Kotlin, Swift, TypeScript and Dart, and a `Chimera العربية` desktop personality. The Arabic contract covers menus, settings, networking, security, storage, drivers, developer tools, diagnostics, accessibility and system actions.

The desktop compatibility model catalogs GNOME, KDE Plasma, Xfce, Cinnamon, MATE and LXQt on Linux, classic through modern Windows/WinUI, and Classic-Mac/Cocoa/AppKit/SwiftUI-era macOS presentation. These are behavior/appearance compatibility profiles rather than copied proprietary source or binaries. Open-source upstream projects remain subject to their own licenses and provenance requirements.

Arabic UI follows Unicode logical text order and uses platform text shaping/BiDi/layout engines rather than manually reversing strings. RTL tests cover mixed Arabic/Latin text, numerals, paths/URLs, keyboard switching, accessibility, clipping, menus, panels, dialogs and clipboard round trips. Microsoft explicitly documents RTL flow and flexible layouts for Arabic, while Apple documents RTL mirroring through standard layout systems and RTL testing. GNOME, KDE Plasma, MATE and LXQt document their respective desktop architectures publicly.

See `desktop/localization/ar-SA.json`, `desktop/upstream_desktop_catalog.json`, `desktop/desktop_profiles.json`, `docs/ARABIC_DESKTOP_AND_LOCALIZATION.md` and `.github/workflows/arabic-desktop-ci.yml`.

## RISC and CISC instruction-set catalog

`isa/catalog.json` is the canonical machine-readable instruction catalog. It enumerates major RISC and CISC families used by real computers, records operand structure including optional operands, and stores a worked binary and hexadecimal encoding for each catalog instruction. Current families include RISC-V, AArch64, ARM32, MIPS32, OpenPOWER, SPARC, x86/Intel 64/AMD64, Motorola 68000, IBM System z and VAX.

The catalog separates concrete encodings from general encoding fields so it can support future assembler/disassembler, emulator and binary-analysis work without confusing an example opcode with a complete instruction decoder. C/C++, Rust, Python, Java, C#, Kotlin, Swift, TypeScript and Dart adapters expose the same canonical dataset. See `docs/ISA_CATALOG.md`, `isa/schema.json`, `tools/validate_isa_catalog.py` and `.github/workflows/isa-catalog-ci.yml`.

## Application networking

`network/ApplicationNetworkModule.md` defines the in-application Network Center for Client, Server, Host (server + local client), P2P and Hybrid modes. Users can choose a nickname and avatar, including a validated local image upload when built-in avatars are unavailable. Spotnik remains the OS networking boundary while application sessions can select QUIC/TLS, TCP/TLS, WebRTC, WebSocket/WebTransport and libp2p adapters.

## Open-source Linux / Windows / macOS services and applications

Chimera II now has a provenance-first compatibility layer for open-source services, desktop technologies and free applications. The canonical source registry is `opensource/sources.json`; service capabilities are defined in `services/service_registry.json`; application compatibility records are in `applications/catalog.json`.

The integration covers Linux systemd/D-Bus/NetworkManager/PipeWire/CUPS/udev/Samba families, Windows Service Control Manager/Task Scheduler/PowerShell/Windows Terminal/WSL/Windows App SDK boundaries, and macOS launchd/POSIX/CoreAudio/WebKit/printing boundaries. Aurora remains the common desktop capability layer, while platform adapters preserve each operating system's distinct semantics.

Application families include file managers, terminals, office/document suites, image/PDF tools, media players, browser/WebKit shells, archives, calculators, system monitors, disk/network/developer tools, accessibility, recording, backup/synchronization and package-management interfaces.

These are compatibility and provenance layers rather than a claim that the repository contains every upstream project. Large upstream projects remain external and are represented by versioned source/license metadata and explicit staging/build manifests. Proprietary platform binaries are not redistributed. Downloaded artifacts are not executed automatically.

## Aurora desktop compatibility

Aurora has a platform-neutral desktop/event layer for **Linux, Windows and macOS**, with historical interaction personalities and native backend boundaries. The canonical schema is `desktop/event_schema.json`; desktop-era profiles are in `desktop/platform_profiles.json`.

Supported compatibility families include Windows Win32 through modern Windows, Linux X11/GTK/Qt/Wayland generations, and macOS AppKit through modern SwiftUI-era presentation. These are behavioral compatibility profiles: Chimera does not copy proprietary operating-system binaries.

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

Chimera II OS is distributed under GNU GPL v3 or later unless a subcomponent explicitly identifies a compatible third-party license. Third-party dependencies and assets retain their original licenses. The open-source compatibility and ISA layers record exact upstream provenance and license expressions instead of assuming that all upstream projects can be relicensed as GPL.
