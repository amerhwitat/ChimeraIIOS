# Chimera II OS

Chimera II OS is a cross-language research operating-system and application platform centered on the Koronos microkernel, wide-register C8192/R8192 research ISA, multidimensional cognition, portable tooling, trusted peer networking and separate Mobile Microkernel/application stacks.

## Core architecture

- **Spit Fire** — BIOS/UEFI boot layer.
- **Jasper** — boot manager.
- **Koronos** — hybrid microkernel and scheduling/IPC platform.
- **Spotnik** — IPv4/IPv6 networking research.
- **Aurora** — graphical desktop/runtime layer.
- **Nucleus / Hive / Kore / Aegis / CEF** — data, state, services, security and compatibility layers.
- **RegisterN / C8192 / R8192** — scalable register and ISA research.
- **Mobile Microkernel + Kotlin Mobile** — isolated mobile platform and Android application boundary.
- **Apple Platform** — SwiftUI/Xcode iOS/iPadOS and macOS application boundary with XcodeGen project generation, xcodebuild archive/export, Kotlin/Native XCFramework integration and optional fastlane automation.

## 128D and authenticated P2P

Applications use the canonical 128D semantic profile and an authenticated opt-in P2P contract with capability negotiation, request/response, pub/sub, snapshot/delta, content-addressed exchange, sequence numbers and payload integrity. The protocol excludes unsolicited scanning, credential/private-key exchange, arbitrary executable transfer and remote command execution.

## Kotlin mobile communications

The Kotlin mobile portfolio includes synchronized text conversations, IRC-style channels, presence/session metadata and a WebRTC-ready voice/video boundary. Android microphone and camera permissions are declared for mobile communication applications and must be requested only when the user starts the corresponding feature. See `docs/MOBILE_COMMUNICATIONS.md`.

BizX and BizXtreme are the primary application integrations, while the same mobile communication contract is available to CPU simulation, NLP/document, crypto-research and integration applications.

## Apple applications and IPA builds

`apple/project.yml` defines native iOS and macOS application targets. `apple/Sources/` contains the SwiftUI shell and shared boundary. On macOS, install Xcode and XcodeGen, run `xcodegen generate`, then archive with `apple/scripts/archive-ios.sh` and export an IPA with `apple/scripts/export-ipa.sh`. `tools/apple/install-apple-toolchain.sh` checks Xcode/Swift and can install XcodeGen through Homebrew; fastlane is an optional open-source automation layer.

Actual IPA compilation/signing requires a macOS/Xcode host. Windows/Linux scripts can prepare or dispatch the build but do not claim Apple binaries were produced locally.

## Automated APK builds

`tools/mobile/install-android-sdk.ps1` provisions the Android CLI/SDK when absent. `build-portfolio-mobile.ps1`, `.cmd` and `.sh` discover Kotlin Android projects across the related repositories and build debug/release APKs. The scripts do not embed credentials or execute arbitrary remote payloads.

## Licensing

Chimera II OS is distributed under GNU GPL v3 or later unless a subcomponent explicitly identifies a compatible third-party license. Third-party dependencies and assets retain their original licenses.
