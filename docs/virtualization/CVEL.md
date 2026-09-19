# Chimera Virtualization & Emulation Layer (CVEL)

CVEL provides one provider-neutral interface for running Chimera guest images and architecture workloads through QEMU, Oracle VirtualBox and VMware where those products are installed.

## Supported provider roles

| Provider | Primary role | Architecture scope |
|---|---|---|
| QEMU | Full-system emulation and virtualization | x86/x86-64, ARM/AArch64, RISC-V, MIPS, PowerPC, SPARC and provider-supported targets |
| VirtualBox | Desktop virtualization | x86/x86-64 |
| VMware | Desktop/server virtualization | x86/x86-64 |

Provider availability is detected at runtime. CVEL never assumes that an external hypervisor is installed.

## Execution model

`CVEL -> machine profile -> provider backend -> guest firmware -> guest OS/runtime`

Execution modes are represented explicitly as interpreter, JIT, hardware-assisted and native. A mode is a capability, not a promise: the backend must verify that the host/provider can actually supply it.

## Safety and provenance

Guest images, firmware, ROMs and drivers remain explicit inputs. CVEL does not silently download untrusted code, flash physical devices, or bypass Secure Boot/AVB/vendor protections.

## CLI

`chimera_vm detect` reports available providers.

`chimera_vm run <name> [disk-image]` generates/uses the QEMU run path for a machine profile.

The backend library is also intended for Aurora UI integration, automated CI boot tests, debugger integration and future C8192/R8192 execution adapters.
