# Chimera II OS

Chimera II OS is a cross-language research operating-system and application platform centered on the Koronos microkernel, wide-register C8192/R8192 research ISA, multidimensional cognition, portable tooling, trusted peer networking and separate Mobile Microkernel/application stacks.

## Canonical source-code index

The README now explicitly cites the implementation areas so architecture claims can be traced to source:

- **Boot:** `Spit Fire` / bootloader sources under the boot and firmware trees.
- **Kernel:** `Koronos` microkernel, scheduler, IPC and synchronization sources.
- **Networking:** `Spotnik` IPv4/IPv6 and transport/networking sources.
- **Desktop:** `Aurora` graphics/windowing/runtime sources.
- **Data/services/security:** `Nucleus`, `Hive`, `Kore`, `Aegis` and `CEF` implementation trees.
- **Registers/ISA:** `RegisterN`, C8192/R8192 and instruction/ABI implementation trees.
- **Mobile:** the separate Mobile Microkernel and application implementation trees.
- **P2P:** authenticated capability/request/response/pub-sub/snapshot-delta protocol sources.
- **AI:** RNN/LLM and neural-memory implementation sources.
- **Automation/tests:** build scripts, ISO tooling, CI and regression tests.

Apple companion source is explicitly maintained in [`general/Apple-Implementations/ChimeraIIOS`](https://github.com/amerhwitat/general/tree/master/Apple-Implementations/ChimeraIIOS), including Objective-C/Xcode specifications and Flutter iOS/macOS application sources.

## Apple Objective-C + Flutter portfolio

The centralized Apple source tree is maintained in [`general/Apple-Implementations/ChimeraIIOS`](https://github.com/amerhwitat/general/tree/master/Apple-Implementations/ChimeraIIOS). It contains Objective-C/Xcode project specifications and Flutter iOS/macOS application sources. Objective-C owns Apple framework/native performance boundaries while Flutter provides the portable UI/application layer.

## Core architecture

- **Spit Fire** — BIOS/UEFI boot layer.
- **Jasper** — boot manager.
- **Koronos** — hybrid microkernel and scheduling/IPC platform.
- **Spotnik** — IPv4/IPv6 networking research.
- **Aurora** — graphical desktop/runtime layer.
- **Nucleus / Hive / Kore / Aegis / CEF** — data, state, services, security and compatibility layers.
- **RegisterN / C8192 / R8192** — scalable register and ISA research.
- **Mobile Microkernel + Kotlin Mobile** — isolated mobile platform and Android application boundary.
- **Apple Platform** — Objective-C/Flutter iOS/iPadOS and macOS companion implementation with XcodeGen and xcodebuild automation.

## 128D and authenticated P2P

Applications use the canonical 128D semantic profile and an authenticated opt-in P2P contract with capability negotiation, request/response, pub/sub, snapshot/delta, content-addressed exchange, sequence numbers and payload integrity. The protocol excludes unsolicited scanning, credential/private-key exchange, arbitrary executable transfer and remote command execution.

## Kotlin mobile communications

The Kotlin mobile portfolio includes synchronized text conversations, IRC-style channels, presence/session metadata and a WebRTC-ready voice/video boundary. Android microphone and camera permissions are declared for mobile communication applications and must be requested only when the user starts the corresponding feature. See `docs/MOBILE_COMMUNICATIONS.md`.

## Apple applications and IPA builds

`apple/project.yml` defines native iOS and macOS application targets. `apple/Sources/` contains the SwiftUI shell and shared boundary. The central Objective-C/Flutter implementations are under the General repository. On macOS, install Xcode and XcodeGen, generate the project, then archive/export with xcodebuild or fastlane. Actual IPA compilation/signing requires macOS/Xcode and operator-controlled signing material.

## Automated APK builds

`tools/mobile/install-android-sdk.ps1` provisions the Android CLI/SDK when absent. `build-portfolio-mobile.ps1`, `.cmd` and `.sh` discover Kotlin Android projects across the related repositories and build debug/release APKs. The scripts do not embed credentials or execute arbitrary remote payloads.

## Licensing

Chimera II OS is distributed under GNU GPL v3 or later unless a subcomponent explicitly identifies a compatible third-party license. Third-party dependencies and assets retain their original licenses.
