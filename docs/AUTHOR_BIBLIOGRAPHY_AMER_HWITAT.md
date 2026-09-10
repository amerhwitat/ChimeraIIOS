# Amer Hwitat — Chimera II OS Research Bibliography

**Author / Researcher:** Amer Hwitat  
**Project:** Chimera II OS  
**Bibliography scope:** research documents and project artifacts available in the Chimera II research corpus.

> This bibliography records the project's own research corpus. It does not claim peer-reviewed publication status unless a source is explicitly identified as such.

## Core Chimera II OS documents

1. **Chimera II OS Comprehensive Redesign, Internet Research, Architecture Specification & Source Blueprint**, Version 2.0, 5 September 2026. The Library copy identifies the document as a research/engineering blueprint and separates implemented host-emulation components from future bare-metal work. fileciteturn66file0L11-L29
2. **Chimera II OS — Mobile & Robotics Research Architecture Report.** Covers the proposed R8192 processor, RISC/CISC execution model, microkernel, V-Core isolation, ARM/x86 compatibility, mobile computing, robotics and distributed intelligence. fileciteturn66file1L57-L67
3. **Chimera II Low-Level Architecture & Implementation Specification v0.1.** Defines the software-defined processor ecosystem, architectural layers, R8192 state, compiler/toolchain, microkernel and firmware targets. fileciteturn72file6L351-L369
4. **Chimera II OS Developer Guide** — consolidated boot, kernel, networking, graphics, database, emulation, CI and test blueprint. The Library version explicitly organizes Spit Fire/Jasper, Koronos/RegisterN, Spotnik, Aurora, CEF and release/testing material. fileciteturn72file4L118-L158
5. **Chimera II OS — crash dump / Developer & Low-Level Technical Guide.** Earlier architecture and implementation notes covering ARM Cortex-M, x86-64, the proposed 8192-bit ISA, networking, boot and toolchain. fileciteturn72file7L417-L454
6. **Chimera II Web Runtime & Desktop Integration.** Research baseline for Aurora Wayland Glass, browser virtualization, desktop profiles, application registry and sandbox boundaries. fileciteturn72file2L65-L81
7. **Integrating Linux 7.x, Retro Emulation, and Future Computing into Chimera II Web OS.** Research survey connecting Linux concepts, browser emulation, desktop profiles and multidimensional computing to Chimera II. fileciteturn72file0L11-L30
8. **8192-ChimeraII-OS-Summary** — architecture and implementation summary in the research archive.
9. **Source-Code** — source-oriented Chimera II research archive referenced by the low-level specification.
10. **CPU4096 / ARM / x86 research documents** — wide-register CPU and compatibility studies.

## Mobile and Aurora research corpus

- **Chimera_II_OS_Mobile_Robotics_Architecture_Report.pdf** — mobile, robotics, edge, distributed intelligence and safety architecture. The mobile section explicitly separates Mobile UI, application API, CPU/GPU/NPU/DSP, Chimera HAL and microkernel/V-Cores. fileciteturn66file3L198-L219
- **Aurora Wayland Glass Desktop.png** — approved visual reference in the Library for Aurora's glass desktop language. fileciteturn67file29L151-L155
- **Aurora Wayland Desktop Showcase.png** — additional Aurora visual reference. fileciteturn67file28L144-L148

## Research principles recorded in the corpus

The research architecture treats the R8192 CPU as a proposal/emulation target rather than existing silicon, and separates register width, instruction encoding width, execution lanes, issue width and memory bandwidth. fileciteturn66file0L20-L29

The mobile/robotics architecture emphasizes deterministic control, parallelism, wide data processing, selective zero-copy, hardware independence and security by isolation. fileciteturn66file4L293-L311

The implementation roadmap is intentionally staged from formal ISA and emulator work through assembler/linker/compiler, host microkernel, x86/UEFI and ARM ports, networking, robotics middleware, accelerator integration and only then FPGA/ASIC feasibility. fileciteturn66file7L503-L519

## Research archive provenance

The repository documentation should distinguish three classes:

1. **Original Amer Hwitat / Chimera II material** — may be published according to the repository license.
2. **Third-party research and standards** — cited and linked; license preserved.
3. **Historical or proprietary source material** — used only as research/provenance where legally permitted; not republished as original Chimera code.

This bibliography is intentionally conservative: it lists identifiable research artifacts from the Library rather than inventing publication venues, DOI numbers, academic affiliations or peer-review claims.
