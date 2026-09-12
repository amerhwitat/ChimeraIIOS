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

## Application networking

`network/ApplicationNetworkModule.md` defines the in-application Network Center for Client, Server, Host (server + local client), P2P and Hybrid modes. Users can choose a nickname and avatar, including a validated local image upload when built-in avatars are unavailable. Spotnik remains the OS networking boundary while application sessions can select QUIC/TLS, TCP/TLS, WebRTC, WebSocket/WebTransport and libp2p adapters.

## Open-source Linux / Windows / macOS services and applications

Chimera II now has a provenance-first compatibility layer for open-source services, desktop technologies and free applications. The canonical source registry is `opensource/sources.json`; service capabilities are defined in `services/service_registry.json`; application compatibility records are in `applications/catalog.json`.

The integration covers Linux systemd/D-Bus/NetworkManager/PipeWire/CUPS/udev/Samba families, Windows Service Control Manager/Task Scheduler/PowerShell/Windows Terminal/WSL/Windows App SDK boundaries, and macOS launchd/POSIX/CoreAudio/WebKit/printing boundaries. Aurora remains the common desktop capability layer, while platform adapters preserve each operating system's distinct semantics.

Application families include file managers, terminals, office/document suites, image/PDF tools, media players, browser/WebKit shells, archives, calculators, system monitors, disk/network/developer tools, accessibility, recording, backup/synchronization and package-management interfaces.

These are compatibility and provenance layers rather than a claim that the repository contains every upstream project. Large upstream projects remain external and are represented by versioned source/license metadata and explicit staging/build manifests. Proprietary platform binaries are not redistributed. Downloaded artifacts are not executed automatically.

See `docs/OPEN_SOURCE_INTEGRATION.md`, `docs/SERVICES_COMPATIBILITY.md`, `docs/APPLICATION_COMPATIBILITY.md` and `docs/SOURCE_PROVENANCE.md`.

## Aurora desktop compatibility

Aurora has a platform-neutral desktop/event layer for **Linux, Windows and macOS**, with historical interaction personalities and native backend boundaries. The canonical schema is `desktop/event_schema.json`; desktop-era profiles are in `desktop/platform_profiles.json`.

Supported compatibility families include Windows Win32 through modern Windows, Linux X11/GTK/Qt/Wayland generations, and macOS AppKit through modern SwiftUI-era presentation. These are behavioral compatibility profiles: Chimera does not copy proprietary operating-system binaries.

The event pipeline is:

`hardware/input → native adapter → CHM event → focus/hit-test/gesture routing → window/widget → command/action`

The event ABI/model is implemented in C, C++, Rust, Python, Java, C#, Kotlin, Swift and TypeScript. See `docs/DESKTOP_COMPATIBILITY.md` and the corresponding language subdirectories under `desktop/`.

## Neural multidimensional reasoning

The `neural/` layer combines weighted evidence, disagreement-aware confidence, observer/perspective transforms and multidimensional feature overlays. The intended response pipeline is **evidence → normalization → geometry → observer transform → neural reasoning → confidence → explanation → optional speech**. This makes perspective separate from geometry and keeps uncertainty explicit.

The 128D profile remains an experimental computational semantic representation, not a claim about the number of physical dimensions.

See `docs/NEURAL_REASONING.md` and `multidimensional/`.

## Voice and speech

`voice/` provides a cross-platform TTS/STT boundary. Providers can target Windows SAPI/WinRT, Linux/Unix Speech Dispatcher/PipeWire/ALSA/PulseAudio, Apple AVFoundation/CoreAudio, or explicitly configured external engines. The core does not silently upload text or audio and does not bundle proprietary speech engines.

See `docs/VOICE.md`.

## Quantum computing research layer

The `quantum/` tree provides a portable CPU-baseline state-vector simulator, QFT/gate primitives, C ABI, versioned `CHMQ-1` circuit IR, Python/Rust reference implementations and adapters for Java, C#, TypeScript, Kotlin, Swift and Dart. Research integration targets include Qiskit, Cirq, PennyLane, NVIDIA CUDA-Q, cuQuantum and qsim. External quantum services remain opt-in. The implementation is clean-room: upstream projects are architectural and mathematical references, not copied source.

See `docs/QUANTUM_SOURCE_PROVENANCE.md`.

## Hardware, GPU and driver compatibility

The `drivers/` layer contains a stable hardware capability registry covering modern and legacy CPU families, GPU families, PCI/PCIe/USB/virtio/NVMe/SATA/SCSI/I2C/SPI/GPIO/Bluetooth classes, networking, audio, cameras, input and display. It also defines protocol-level printer support including IPP Everywhere, PostScript, PCL5/PCL6, ESC/P, ESC/POS, PDF/PS and a deterministic **Ghost Printer** virtual sink.

Chimera II can discover, acquire, verify and stage Linux and Windows driver candidates through a security-first broker. It never silently loads downloaded code, bypasses Secure Boot/signature enforcement, or treats proprietary driver binaries as redistributable merely because they can be found online.

## Licensing and provenance

Chimera II OS is distributed under GNU GPL v3 or later unless a subcomponent explicitly identifies a compatible third-party license. Third-party dependencies and assets retain their original licenses. The new open-source compatibility layer records exact upstream provenance and license expressions instead of assuming that all upstream projects can be relicensed as GPL.
