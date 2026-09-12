# Chimera II OS

Chimera II OS is a cross-language research operating-system and application platform centered on the Koronos microkernel, wide-register C8192/R8192 research ISA, multidimensional cognition, portable tooling, trusted peer networking and separate Mobile Microkernel/application stacks.

## Application networking

`network/ApplicationNetworkModule.md` defines the new in-application Network Center for Client, Server, Host (server + local client), P2P and Hybrid modes. Users can choose a nickname and avatar, including a validated local image upload when built-in avatars are unavailable. Spotnik remains the OS networking boundary while application sessions can select QUIC/TLS, TCP/TLS, WebRTC, WebSocket/WebTransport and libp2p adapters.

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

## Open-source Linux / Windows / macOS services and applications

Chimera II now has a provenance-first compatibility layer for open-source services, desktop technologies and free applications. The canonical source registry is `opensource/sources.json`; service capabilities are defined in `services/service_registry.json`; application compatibility records are in `applications/catalog.json`.

## Neural multidimensional reasoning

The `neural/` layer combines weighted evidence, disagreement-aware confidence, observer/perspective transforms and multidimensional feature overlays. The 128D profile remains an experimental computational semantic representation, not a claim about the number of physical dimensions.

## Voice and speech

`voice/` provides a cross-platform TTS/STT boundary.

## Quantum computing research layer

The `quantum/` tree provides a portable CPU-baseline state-vector simulator, QFT/gate primitives, C ABI, versioned `CHMQ-1` circuit IR, Python/Rust reference implementations and adapters for Java, C#, TypeScript, Kotlin, Swift and Dart.

## Hardware, GPU and driver compatibility

The `drivers/` layer contains a stable hardware capability registry covering modern and legacy CPU families, GPU families, PCI/PCIe/USB/virtio/NVMe/SATA/SCSI/I2C/SPI/GPIO/Bluetooth classes, networking, audio, cameras, input and display.

## Licensing and provenance

Chimera II OS is distributed under GNU GPL v3 or later unless a subcomponent explicitly identifies a compatible third-party license. Third-party dependencies and assets retain their original licenses.
