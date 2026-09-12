# Chimera II OS

Chimera II OS is a cross-language research operating-system and application platform centered on the Koronos microkernel, wide-register C8192/R8192 research ISA, multidimensional cognition, portable tooling, trusted peer networking and separate Mobile Microkernel/application stacks.

## Complete source-code citation index

| Area | Source |
|---|---|
| Boot / Spit Fire | [boot and firmware trees](.) |
| Jasper boot manager | [boot-manager sources](.) |
| Koronos microkernel | [kernel sources](.) |
| Spotnik networking | [networking sources](.) |
| Aurora desktop | [`desktop/`](desktop/) |
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

## Aurora desktop compatibility

Aurora now has a platform-neutral desktop/event layer for **Linux, Windows and macOS**, with historical interaction personalities and native backend boundaries. The canonical schema is `desktop/event_schema.json`; desktop-era profiles are in `desktop/platform_profiles.json`.

Supported compatibility families include Windows Win32 through modern Windows, Linux X11/GTK/Qt/Wayland generations, and macOS AppKit through modern SwiftUI-era presentation. These are behavioral compatibility profiles: Chimera does not copy proprietary operating-system binaries.

The event pipeline is:

`hardware/input → native adapter → CHM event → focus/hit-test/gesture routing → window/widget → command/action`

The event ABI/model is implemented in C, C++, Rust, Python, Java, C#, Kotlin, Swift and TypeScript. See `docs/DESKTOP_COMPATIBILITY.md` and the corresponding language subdirectories under `desktop/`.

## Neural multidimensional reasoning

The `neural/` layer combines weighted evidence, disagreement-aware confidence, observer/perspective transforms and multidimensional feature overlays. The intended response pipeline is **evidence → normalization → geometry → observer transform → neural reasoning → confidence → explanation → optional speech**. This makes perspective separate from geometry and keeps uncertainty explicit.

The 128D profile remains an experimental computational semantic representation, not a claim about the number of physical dimensions.

See `docs/NEURAL_REASONING.md` and `multidimensional/`.

## Voice and speech

`voice/` provides a cross-platform TTS/STT boundary. Providers can target Windows SAPI/WinRT, Linux/Unix Speech Dispatcher/PipeWire/ALSA/PulseAudio compatibility, Apple AVFoundation/CoreAudio, or explicitly configured external engines. The core does not silently upload text or audio and does not bundle proprietary speech engines.

See `docs/VOICE.md`.

## Quantum computing research layer

The `quantum/` tree provides a portable CPU-baseline state-vector simulator, QFT/gate primitives, C ABI, versioned `CHMQ-1` circuit IR, Python/Rust reference implementations and adapters for Java, C#, TypeScript, Kotlin, Swift and Dart. Research integration targets include Qiskit, Cirq, PennyLane, NVIDIA CUDA-Q, cuQuantum and qsim. External quantum services remain opt-in.

The implementation is clean-room: upstream projects are architectural and mathematical references, not copied source. See `docs/QUANTUM_SOURCE_PROVENANCE.md`.

## Hardware, GPU and driver compatibility

The `drivers/` layer contains a stable hardware capability registry covering modern and legacy CPU families, GPU families, PCI/PCIe/USB/virtio/NVMe/SATA/SCSI/I2C/SPI/GPIO/Bluetooth classes, networking, audio, cameras, input and display. It also defines protocol-level printer support including IPP Everywhere, PostScript, PCL5/PCL6, ESC/P, ESC/POS, PDF/PS and a deterministic **Ghost Printer** virtual sink.

Chimera II can discover, acquire, verify and stage Linux and Windows driver candidates through a security-first broker. It never silently loads downloaded code, bypasses Secure Boot/signature enforcement, or treats proprietary driver binaries as redistributable merely because they can be found online.

## Rust implementation

`rust/ChimeraIIOS/` is a separate Rust workspace with core, register, ISA, quantum, multidimensional, neural, voice, driver and CLI crates. It remains a safe user-space/runtime research implementation; bootloader/kernel integration is a separate freestanding target requiring hardware/ABI validation.

## Perspective vs geometry and equations

Geometry uses vectors, tensor contraction and affine transformations. Perspective uses observer origin, projection and uncertainty/perception overlays:

`x' = A x + b`, `r = x-o`, `p = P r`, `C_ik = sum_j A_ij B_jk`.

For weighted evidence `S = sum(w_i e_i)/sum(w_i)` and a conservative spread-aware confidence `C = clamp(S(1-sqrt(V)),0,1)` with `V = sum(w_i(e_i-S)^2)/sum(w_i)`.

## Core architecture

- **Spit Fire** — BIOS/UEFI boot layer.
- **Jasper** — boot manager.
- **Koronos** — hybrid microkernel and scheduling/IPC platform.
- **Spotnik** — IPv4/IPv6 networking research.
- **Aurora** — graphical desktop/runtime and cross-platform desktop personality layer.
- **Nucleus / Hive / Kore / Aegis / CEF** — data, state, services, security and compatibility layers.
- **RegisterN / C8192 / R8192** — scalable register and ISA research.
- **Mobile Microkernel** — isolated mobile platform boundary.

## Licensing and provenance

Chimera II OS is distributed under GNU GPL v3 or later unless a subcomponent explicitly identifies a compatible third-party license. Third-party dependencies and assets retain their original licenses. Source provenance is documented in `docs/QUANTUM_SOURCE_PROVENANCE.md`, `docs/DRIVER_ARCHITECTURE.md`, `docs/HARDWARE_DRIVER_SOURCE_PROVENANCE.md`, `docs/DRIVER_ACQUISITION.md` and `docs/DESKTOP_COMPATIBILITY.md`.
