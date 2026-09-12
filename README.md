# Chimera II OS

Chimera II OS is a cross-language research operating-system and application platform centered on the Koronos microkernel, wide-register C8192/R8192 research ISA, multidimensional cognition, portable tooling, trusted peer networking and separate Mobile Microkernel/application stacks.

## Complete source-code citation index

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
| Neural reasoning | [`neural/`](neural/) |
| Voice / speech | [`voice/`](voice/) |
| Hardware / GPU / driver registry | [`drivers/`](drivers/) |
| Java hardware/driver layer | [`java/`](java/) |
| Rust implementation | [`rust/ChimeraIIOS/`](rust/ChimeraIIOS/) |
| Mobile Microkernel | [mobile sources](.) |
| P2P | [protocol sources](.) |
| Automation / ISO / tests | [tools, build and test trees](.) |
| Complete tracked repository | [full source tree](.) |

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

The `drivers/` layer contains a stable hardware capability registry covering modern and legacy CPU families, GPU families (NVIDIA, AMD, Intel, Apple, ARM Mali, Qualcomm Adreno, PowerVR, 3dfx, Matrox, S3, VIA, SiS and virtual GPUs), PCI/PCIe/USB/virtio/NVMe/SATA/SCSI/I2C/SPI/GPIO/Bluetooth classes, networking, audio, cameras, input and display.

It also defines protocol-level printer support including IPP Everywhere, PostScript, PCL5/PCL6, ESC/P, ESC/POS, PDF/PS and a deterministic **Ghost Printer** virtual sink.

### Driver acquisition

Chimera II can now **discover, acquire, verify and stage Linux and Windows driver candidates** through a security-first broker. The flow is:

`hardware probe → source discovery → hardware-ID matching → HTTPS acquisition → SHA-256 verification → signature/trust check → license/provenance → quarantine/staging → explicit installation`

Linux `.ko` modules are accepted only when their declared kernel ABI matches the Koronos policy; otherwise source/package metadata is routed through the Chimera driver-port layer. Windows INF/CAT/SYS packages are treated as Driver Store candidates and final installation is delegated to the platform's trusted installation mechanism.

The acquisition layer never silently loads downloaded code, never disables Secure Boot/signature enforcement, and never treats proprietary driver binaries as redistributable merely because they can be found online. Curated source metadata lives in `drivers/acquisition_sources.json`; the Java equivalent is under `java/chimera/drivers/acquisition/`.

See `docs/DRIVER_ACQUISITION.md`, `docs/DRIVER_ARCHITECTURE.md`, `docs/DRIVER_WINDOWS_LINUX_UNIX.md` and `drivers/hardware_registry.json`.

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
- **Aurora** — graphical desktop/runtime layer.
- **Nucleus / Hive / Kore / Aegis / CEF** — data, state, services, security and compatibility layers.
- **RegisterN / C8192 / R8192** — scalable register and ISA research.
- **Mobile Microkernel** — isolated mobile platform boundary.

## Licensing and provenance

Chimera II OS is distributed under GNU GPL v3 or later unless a subcomponent explicitly identifies a compatible third-party license. Third-party dependencies and assets retain their original licenses. Source provenance is documented in `docs/QUANTUM_SOURCE_PROVENANCE.md`, `docs/DRIVER_ARCHITECTURE.md`, `docs/HARDWARE_DRIVER_SOURCE_PROVENANCE.md` and `docs/DRIVER_ACQUISITION.md`.
