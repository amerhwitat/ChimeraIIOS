# CHIMERA II — Integrated Architecture

## Purpose

This document integrates the high-level architecture with the Developer Guide source tree. The design is deliberately split into **Machine**, **Cognitive**, and **World** planes. The kernel controls resources and isolation; intelligence remains above the kernel.

## Machine plane

- R8192: 1024 × 8192-bit general registers, represented as 128 × 64-bit lanes.
- C8192: variable-length instruction packets and micro-op expansion.
- Tensor/vector/crypto execution interfaces.
- Host execution targets: x86-64 and ARM64; future FPGA/hardware targets remain research goals.

## Cognitive plane

`State128` represents a 128-dimensional computational state. It is not a claim of 128 physical dimensions.

```text
Observation → 128D State → Memory → Knowledge → Reasoning → Planning → Action → Observation
```

Memory levels: CPU state, working memory, episodic memory, semantic memory, persistent knowledge.

The evidence model distinguishes `FACT`, `OBSERVATION`, `MODEL`, `HYPOTHESIS`, `INTERPRETATION`, `SPECULATION`, and `UNKNOWN`.

## World plane

Networking, storage, GPU/compositor, sensors, cameras, external APIs and human interfaces live here. Spotnik provides a zero-copy networking boundary; Aurora provides the graphics boundary.

## Kernel

Koronos remains small: process/thread management, scheduling, virtual memory, IPC, interrupts/timers, capabilities, DMA and device abstraction. AI reasoning, natural-language processing and scientific inference do not belong in the kernel.

## Chronos

Scheduling is modeled as resource-aware orchestration:

`score = f(priority, deadline, dependency, energy, locality, accelerator, confidence)`

The current implementation is a deterministic skeleton; production scheduling requires workload measurements and formal validation.

## Boot

Preferred production path: UEFI/GPT → Spit Fire → Jasper → Koronos. BIOS/MBR remains a compatibility path. QEMU is the first validation environment.

## Graphics

Aurora targets Wayland-style presentation, 4D rotations (`Rxw`, `Rzw`), GPU post-processing, zero-copy DMA-BUF/EGL paths and selective damage/repaint. Compute-shader blur is kept as an optional experimental effect.

## Networking

The target stack is IPv6-first dual stack with TCP/UDP, routing/ND, DHCPv6/SLAAC and IPv4 compatibility. AF_XDP/libxsk and Netmap are backends; IOMMU-aware DMA and capability checks are mandatory for privileged paths.

## Data

Nucleus is the HTAP/data-engine boundary; TensorFS is the wide-state/object-oriented storage concept; Hive is the configuration/registry boundary.

## Emulation

CEF launches sandboxed services from explicit manifests. ROM/BIOS material and third-party cores require provenance and license checks.

## Engineering status

The repository contains host-side prototypes and interface skeletons. Bare-metal boot, a production microkernel, full TCP/IP, a complete Wayland compositor, FPGA implementation and dedicated 8192-bit silicon are future engineering targets rather than completed claims.
