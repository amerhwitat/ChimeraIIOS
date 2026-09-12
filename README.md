# Chimera II OS

Chimera II OS is a cross-language research operating-system and application platform centered on the Koronos microkernel, wide-register C8192/R8192 research ISA, multidimensional cognition, portable tooling, and trusted peer networking.

## Repository scope

This repository contains the computer edition, Mobile Microkernel edition, boot/ISO tooling, desktop/runtime components, database and service layers, ISA/register research, Visual Studio/CMake build material, documentation and application integration.

## Core architecture

- **Spit Fire** — BIOS/UEFI boot layer and boot ABI.
- **Jasper** — boot manager / chain-loading and verification layer.
- **Koronos** — hybrid microkernel and scheduling/IPC research platform.
- **Spotnik** — IPv4/IPv6 networking stack and zero-copy networking research.
- **Aurora** — graphical desktop/runtime layer.
- **Nucleus** — in-memory/disk HTAP database research layer.
- **Hive** — registry/environment/configuration state.
- **Kore** — service/system management.
- **Aegis** — security boundary and trust policy.
- **CEF** — compatibility/emulation framework.
- **RegisterN / C8192 / R8192** — scalable register and ISA research.

## 128D multidimensional application framework

All Chimera applications can use the canonical multidimensional profile in [`docs/CHIMERA_128D_APPLICATION_PROFILE.md`](docs/CHIMERA_128D_APPLICATION_PROFILE.md). The baseline covers point/geometry, planes and relationships, width/height/depth, time, observer/perspective, light/shadow/material response, events, objects/properties/interaction rules and an extensible perception/cognition/information layer.

The 128D framework is semantic: an implementation does not need to allocate a literal 128-element structure when only a subset is needed. Applications declare active dimensions and may extend beyond 128 dimensions using namespaced extensions.

## Authenticated P2P fabric

The canonical peer protocol is [`docs/CHIMERA_P2P_PROTOCOL.md`](docs/CHIMERA_P2P_PROTOCOL.md). It provides opt-in peer identity, capability negotiation, authenticated synchronization, request/response, pub/sub, snapshot/delta and content-addressed exchange. Sequence numbers, payload hashes and optional signatures provide deterministic integrity mechanisms.

The protocol explicitly excludes unsolicited network scanning, credential/private-key exchange, arbitrary executable transfer and remote command execution. Trust policy remains under the local node/application security boundary.

The new ecosystem-level contract is also documented in [`docs/CHIMERA_128D_P2P_INTEROPERABILITY.md`](docs/CHIMERA_128D_P2P_INTEROPERABILITY.md), defining transport-independent state exchange and native language mappings.

## Kotlin mobile portfolio

The portfolio now includes isolated Android/Kotlin mobile implementations for the related applications. See [`docs/KOTLIN_MOBILE_PORTFOLIO.md`](docs/KOTLIN_MOBILE_PORTFOLIO.md). Each application keeps its existing native language implementation and adds a `kotlin/mobile/` entry point. The mobile baseline uses Kotlin 2.4.20, Android Gradle Plugin 9.4.0, SDK 36 and JDK 17, with cleartext traffic disabled by default. The structure is intentionally compatible with a later Kotlin Multiplatform/iOS expansion.

## Portfolio integration

The cross-repository mapping is maintained in [`docs/CHIMERA_PORTFOLIO_INTEGRATION_MATRIX.md`](docs/CHIMERA_PORTFOLIO_INTEGRATION_MATRIX.md). Language implementations remain native to C/C++, C#, Java, Node.js, Python, JavaScript/TypeScript and assembly where appropriate, while interoperability is defined by shared schemas and conformance vectors.

## Build

The repository provides CMake and Visual Studio solutions plus GitHub Actions for the major build paths. See the relevant subdirectory README files before building a specific edition or tool. Kotlin mobile projects are independently buildable from their respective `kotlin/mobile/` directories in Android Studio.

## Licensing

Chimera II OS is distributed under GNU GPL v3 or later unless a subcomponent explicitly identifies a compatible third-party license. Third-party dependencies and assets retain their original licenses.
