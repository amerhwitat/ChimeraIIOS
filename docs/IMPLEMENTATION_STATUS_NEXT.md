# Chimera II OS — Next Implementation Status

This document tracks the implementation layer added after the building-block architecture.

## Completed in this tranche

- Building-block contract smoke tests for boot, memory/DMA, scheduler and capability IPC.
- RegisterN micro-op execution boundary for the canonical runtime layer.
- Mobile architecture HAL contract for AArch64/RISC-V64, timer, power and DMA boundaries.
- CI entry point for building and testing the building-block layer is planned under `.github/workflows/`.

## Execution model

The implementation uses a layered boundary:

1. Firmware/boot handoff → `BootInfo`.
2. Physical memory/DMA → memory contracts.
3. Kernel scheduling/capabilities/IPC → Koronos contracts.
4. RegisterN/C8192/R8192 → micro-op runtime.
5. Mobile HAL → AArch64/RISC-V64 platform boundary.
6. Services such as Spotnik, Nucleus, Hive and Aurora remain outside the privileged microkernel boundary.

## Evidence-backed maturity and SMP

The project now maintains `docs/validation/capability-evidence.json`, validated by `tools/validation/validate_capability_status.py`. Required distinctions: documented ≠ implemented; cataloged ≠ executable; compiled ≠ booted; booted ≠ userspace-ready; sequential multi-CPU simulation ≠ genuine SMP. Genuine SMP remains not verified pending AP bring-up, concurrent execution on at least two CPUs, inter-CPU synchronization/IPI tests, and stress logs. See [Implementation Evidence and Real SMP](IMPLEMENTATION_EVIDENCE_AND_REAL_SMP.md).

## Verification status

GitHub Actions is the authoritative remote build/test environment for this repository when a workflow is present and a run has completed. Local compilation is not claimed unless a local toolchain execution has actually been performed.

The implementation deliberately distinguishes **architecture contracts and executable prototypes** from production hardware support. Real AArch64/RISC-V64 exception entry, MMU setup, interrupt-controller drivers and SoC-specific power sequencing require target hardware/firmware validation.

## Provenance

The implementation follows the repository source-import policy. Public standards and compatible open-source material may inform interfaces; proprietary, leaked, confidential or trade-secret source is excluded.
