# Mobile Microkernel Source and Compatibility Policy

The Mobile Microkernel follows the same source-provenance and clean-room rules as the Computer Edition.

## Linux/mobile ecosystem

Linux-derived concepts may be implemented through documented interfaces, reviewed GPL-compatible components, or independent clean implementations. Android/Linux userspace and device ecosystems are treated as external compatibility targets; their complete source trees are not copied into the privileged Mobile Microkernel.

The privileged core remains small and capability-oriented. Display, input, storage, audio, camera, sensors, USB, Wi-Fi, Bluetooth and cellular functions belong behind driver/service boundaries.

## Windows compatibility

No leaked or confidential Windows source is used. Mobile compatibility code is independently implemented from public API/ABI documentation and legally redistributable materials.

## ISA portability

The mobile target prioritizes AArch64 and RISC-V64. Foreign CPU instructions are translated through a canonical micro-op boundary rather than inserted into the native mobile ISA. LLVM's architecture documentation is used as a reference for portable compiler/backend integration.

## Verification requirements

Every imported or adapted component must have provenance, license metadata, architecture tests, capability checks, and a clear `native`, `emulated`, `adapter`, `reference`, or `planned` status.
