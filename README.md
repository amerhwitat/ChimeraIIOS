# Chimera II OS

Chimera II OS is a cross-language research operating-system and application platform centered on the Koronos microkernel, wide-register C8192/R8192 research ISA, multidimensional cognition, portable tooling, trusted peer networking and separate Mobile Microkernel/application stacks.

## Complete source-code citation index

The README is the source-navigation index for the complete repository. Every major implementation area is cited by its canonical source tree, while component READMEs and source files provide deeper file-level citations.

| Area | Source |
|---|---|
| Boot / Spit Fire | [boot and firmware trees](.) |
| Jasper boot manager | [boot-manager sources](.) |
| Koronos microkernel | [kernel sources](.) |
| Spotnik networking | [networking sources](.) |
| Aurora desktop | [desktop/runtime sources](.) |
| Nucleus / Hive / Kore / Aegis / CEF | [system service trees](.) |
| RegisterN / C8192 / R8192 | [ISA/register sources](.) |
| Quantum computing | [`quantum/`](quantum/) |
| Multidimensional / perspective mathematics | [`multidimensional/`](multidimensional/) |
| Rust implementation | [`rust/ChimeraIIOS/`](rust/ChimeraIIOS/) |
| Mobile Microkernel | [mobile sources](.) |
| P2P | [protocol sources](.) |
| RNN/LLM / neural memory | [AI sources](.) |
| Automation / ISO / tests | [tools, build and test trees](.) |
| Apple companion | [General Apple implementation](https://github.com/amerhwitat/general/tree/master/Apple-Implementations/ChimeraIIOS) |
| Complete tracked repository | [full source tree](.) |

## Quantum computing research layer

The `quantum/` tree provides a portable CPU-baseline state-vector simulator, QFT/gate primitives, C ABI, versioned `CHMQ-1` circuit IR, Python/Rust reference implementations and adapters for Java, C#, TypeScript, Kotlin, Swift and Dart. Research integration targets include Qiskit, Cirq, PennyLane, NVIDIA CUDA-Q, cuQuantum and qsim. External quantum services remain opt-in.

The implementation is clean-room: upstream projects are used as architectural and mathematical references, not as copied source. See `docs/QUANTUM_SOURCE_PROVENANCE.md` for provenance and license policy.

Research ISA metadata defines `QINIT`, `QGATE`, `QCONTROL`, `QMEASURE`, `QTENSOR` and `QSYNC`. These are research-level operation descriptors and do not change the existing boot ABI.

See `docs/QUANTUM_COMPUTING.md`, `quantum/circuit_schema.json` and `docs/QUANTUM_SOURCE_PROVENANCE.md`.

## Perspective vs geometry and 128D mathematics

The `multidimensional/` tree separates geometry from perspective: vectors, tensor contraction and affine transformations form the geometry layer; observer origin, projection and uncertainty/perception overlays form the perspective layer. The 128D model is explicitly treated as an experimental computational semantic representation, not as an established claim that physical spacetime has 128 observable dimensions.

See `docs/MULTIDIMENSIONAL_PERSPECTIVE.md`, `multidimensional/README.md` and `multidimensional/equations.md`.

## Rust implementation

`rust/ChimeraIIOS/` is a separate Rust workspace with `chm-core`, `chm-register`, `chm-isa`, `chm-quantum`, `chm-multidim` and `chm-cli`. The Rust quantum crate now contains a dependency-free state-vector core with X/Y/Z/H/phase gates and normalization tests. It is currently a safe user-space/runtime research implementation; bootloader/kernel integration remains a distinct freestanding target requiring hardware/ABI validation.

See `docs/RUST_IMPLEMENTATION.md` and `docs/superpowers/plans/2026-09-13-quantum-rust-multidim-implementation.md`.

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

`apple/project.yml` defines native iOS and macOS application targets. `apple/Sources/` contains the SwiftUI shell and shared boundary. The central Objective-C/Flutter implementations are under the General repository. On macOS, install Xcode and XcodeGen, generate the project, and archive/export with xcodebuild or fastlane. Actual IPA compilation/signing requires macOS/Xcode and operator-controlled signing material.

## Automated APK builds

`tools/mobile/install-android-sdk.ps1` provisions the Android CLI/SDK when absent. `build-portfolio-mobile.ps1`, `.cmd` and `.sh` discover Kotlin Android projects across the related repositories and build debug/release APKs. The scripts do not embed credentials or execute arbitrary remote payloads.

## Licensing

Chimera II OS is distributed under GNU GPL v3 or later unless a subcomponent explicitly identifies a compatible third-party license. Third-party dependencies and assets retain their original licenses.
