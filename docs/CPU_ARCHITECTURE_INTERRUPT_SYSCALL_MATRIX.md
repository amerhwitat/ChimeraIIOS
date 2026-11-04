# CPU Architecture, Interrupt and Syscall Compatibility Matrix

Status date: 2026-11-04  
Scope: ChimeraIIOS / Koronos and the vendored Koronos integration in OctavianOS.

## Contract

This matrix is an architecture registry and implementation plan, not a claim that every listed CPU can boot Koronos. A row marked **reference-only** is catalogued for research and future porting; it is not a supported boot target. A CPU is eligible for native boot only after its boot protocol, MMU, exception entry, interrupt controller, timer, SMP, syscall ABI, context switch, toolchain and QEMU/physical-hardware tests are implemented.

CISC/RISC are ISA-family descriptions, not dispatch keys. Runtime dispatch must use the normalized architecture plus vendor/implementer, family/model/part, revision, privilege level, feature bitmap, topology and firmware description. Do not infer an architecture from a marketing CPU name alone.

Linux is the primary implementation workflow reference. XNU is a secondary comparison for the two architectures it documents as supported (x86_64 and arm64); macOS/XNU does not provide a RISC-V, PowerPC or general Linux-architecture backend. Linux syscall numbers and calling conventions must never be reused as Koronos ABI numbers.

## Architecture and ABI matrix

| ISA family | Linux architecture / representative CPUs | Exception and interrupt entry model | Linux syscall entry and register ABI (summary) | Koronos status at this revision | macOS/XNU comparison |
|---|---|---|---|---|---|
| CISC | x86_64: Intel/AMD 64-bit, compatible CPUs | IDT gates; CPU exception frames; local APIC / IO-APIC or x2APIC; NMI and local timer paths | `SYSCALL`; number RAX; args RDI, RSI, RDX, R10, R8, R9; result RAX; `SYSRETQ`/IRET return paths | **Partial / experimental**: x86-64 boot and interrupt-frame code exists; a CPL3 INT 0x80 acknowledgement path is present in current candidate work. Full process-owned fd/VFS syscall service, production lifecycle and release acceptance remain separate gates. | XNU has x86_64 machine-dependent trap/interrupt and BSD/Mach syscall paths. Compare source; do not copy private syscall numbers. |
| CISC | i386: Intel/AMD 32-bit x86 | IDT; PIC or APIC; privilege transitions via interrupt/trap gates | `int 0x80` or `SYSENTER`; number EAX; args EBX, ECX, EDX, ESI, EDI, EBP; result EAX | **Reference-only**: no 32-bit Koronos boot/entry backend verified | Historical XNU x86 support is not a current i386 target |
| CISC | m68k: Motorola 680x0 | Vector table, synchronous traps and autovectors; platform interrupt controller | `trap #0`; Linux ABI uses D0 for number and architecture-defined data/address registers for arguments | **Reference-only** | No XNU backend |
| CISC | s390x / s390: IBM Z | Program, supervisor-call, external and I/O interruption classes; lowcore interruption state | `svc`; Linux ABI is architecture-specific (SVC number/register convention); use the kernel syscall table and ABI headers as authority | **Reference-only** | No XNU backend |
| CISC | Alpha: DEC Alpha | PALcode-assisted exception/interrupt entry and processor-specific vectors | `callsys`; V0 syscall number; A0-A5 arguments; architecture-defined error/result convention | **Reference-only** | No XNU backend |
| RISC | arm64 / AArch64: Arm Cortex-A, Neoverse, Apple Silicon | Exception-level vector table; synchronous exceptions, IRQ/FIQ; GICv2/v3/v4 or platform controller | `SVC #0`; X8 number; X0-X5 arguments; X0 result; EL0↔EL1 transition | **Reference-only**: no Koronos AArch64 entry, GIC or context-switch backend verified | XNU supports arm64 and uses its own machine-dependent exception and Mach/BSD syscall layers. Apple Silicon belongs here; it is not x86. |
| RISC | arm / AArch32: Cortex-A/R and supported SoCs | Vector table; IRQ/FIQ; GIC or SoC interrupt controller; exception modes | `SVC`; EABI uses R7 number, R0-R6 arguments, R0 result (ABI variants must be explicit) | **Reference-only** | No current XNU 32-bit ARM target |
| RISC | riscv64 / riscv32: RV64/RV32 implementations | `stvec` trap entry; supervisor exceptions/interrupts; SBI firmware boundary; PLIC or APLIC+IMSIC depending on platform | `ecall`; A7 number; A0-A5 arguments; A0 result | **Reference-only**: no Koronos RISC-V boot, trap, SBI, timer or PLIC/IMSIC backend verified | No XNU backend |
| RISC | powerpc / powerpc64 / powerpc64le: POWER and embedded PowerPC | Exception vector prefixes; external/decrementer interrupts; controller varies (XICS/XIVE, MPIC, etc.) | `sc`; R0 syscall number and R3-R8 arguments in the Linux ABI; return/error convention is architecture-specific | **Reference-only** | No XNU backend |
| RISC | MIPS o32/n32/n64: MIPS32/64 systems | CP0 exception vectors and Cause/Status state; controller platform-dependent | `syscall`; V0 number; A0-A3 initial arguments (additional ABI-specific handling); V0 result | **Reference-only** | No XNU backend |
| RISC | SPARC / SPARC64: LEON and SPARC systems | Trap table and trap-level register windows; platform interrupt controller | `ta` trap entry; register-window and syscall ABI are architecture-specific; consume Linux UAPI tables rather than assuming x86 registers | **Reference-only** | No XNU backend |
| RISC | LoongArch64: Loongson | Exception entry via EENTRY/exception state; IRQ controller hierarchy (e.g. HTVEC/PLIC-style platform blocks) | `syscall`; A7 number, A0-A5 arguments, A0 result in the Linux ABI | **Reference-only** | No XNU backend |
| RISC | ARC: Synopsys ARC | Architecture exception vectors and ARC interrupt controller | ARC-specific trap/syscall ABI; source from Linux arch/arc syscall entry and UAPI | **Reference-only** | No XNU backend |
| RISC | OpenRISC: OpenRISC 1000 | Exception vector table and PIC | Architecture-specific syscall trap/register ABI; source from Linux arch/openrisc | **Reference-only** | No XNU backend |
| RISC | PA-RISC: HP PA-RISC | Processor interruption vectors and external interrupt subsystem | Linux gateway/syscall ABI is PA-RISC-specific; source from arch/parisc entry and UAPI | **Reference-only** | No XNU backend |
| RISC | Nios II: Intel/Altera soft-core | Exception vector and internal/external interrupt controller | Architecture-specific trap/register ABI; source from Linux arch/nios2 | **Reference-only** | No XNU backend |
| RISC | MicroBlaze: AMD/Xilinx soft-core | Exception vector and interrupt controller | Architecture-specific syscall trap/register ABI; source from Linux arch/microblaze | **Reference-only** | No XNU backend |
| RISC | Xtensa: configurable Tensilica cores | Configurable exception levels/vectors and interrupt levels | Xtensa Linux syscall entry and ABI; configuration-dependent | **Reference-only** | No XNU backend |
| RISC | SuperH: SH-2/3/4 families | Exception vectors and interrupt priorities | `trapa` syscall entry; ABI defined by Linux arch/sh | **Reference-only** | No XNU backend |
| RISC | C-SKY: CK series | Exception vectors and interrupt controller | C-SKY-specific syscall trap/register ABI; source from Linux arch/csky | **Reference-only** | No XNU backend |
| RISC | Hexagon: Qualcomm DSP | Vectored exceptions/interrupts and DSP-specific control state | Hexagon-specific syscall entry and register ABI; source from Linux arch/hexagon | **Reference-only** | No XNU backend |

The Linux architecture index is the authoritative discovery list for maintained architecture documentation. The table deliberately summarizes ABI entry points; exact syscall numbers, compat ABIs, argument extensions, error encoding and register clobbers must be generated from the matching Linux UAPI/syscall tables and ISA manuals, not copied from this summary.

## CPU identification and dispatch table

| Architecture | Primary identification inputs | Secondary capability inputs | Interrupt-controller / platform discovery | Required Koronos detector output |
|---|---|---|---|---|
| x86 / x86_64 | CPUID vendor string, base/extended family, model, stepping; CPUID leaf availability | CPUID feature leaves, XSAVE/XCR0, address widths, topology leaves, microcode revision where available | ACPI MADT, MP tables fallback, APIC IDs, HPET/PM timer; PCI enumeration for devices | arch=x86[_64], vendor, family, model, stepping, physical/virtual address bits, feature bitmap, BSP/APIC ID, logical topology, timer and APIC mode |
| ARM / arm64 | MIDR_EL1 implementer, variant, architecture, part number and revision; firmware/DT compatible | ID_AA64* feature registers or AArch32 ID registers; cache/MMU/PA range, SVE/SME only after OS-state support | ACPI MADT/IORT or Device Tree; GIC discovery; PSCI for power/SMP | arch=arm/arm64, implementer, part, revision, EL support, MMU/PA range, feature bitmap, MPIDR affinity, GIC version, PSCI availability |
| RISC-V | MXL and ISA string; MVENDORID, MARCHID, MIMPID when implemented; hart ID | MISA plus SBI extension discovery; per-hart ISA extensions and vector state | Device Tree/ACPI; SBI; PLIC or APLIC+IMSIC; timer interface | arch=riscv32/64, vendor/arch/impl IDs, hart ID, per-hart extension bitmap, privilege modes, SBI version/extensions, interrupt/timer controller |
| PowerPC | PVR processor version/revision; firmware CPU nodes | Facility and vector feature registers, MMU mode | Device Tree/RTAS/OPAL; XICS/XIVE/MPIC | arch, PVR, facilities, MMU, interrupt mode, logical CPU IDs |
| MIPS | PRId implementation/revision and Config registers | ISA/ASE, MMU/TLB and cache configuration | Device Tree/ACPI/platform tables; GIC or SoC controller | arch, PRId, ISA/ASE bitmap, MMU/TLB properties, interrupt source |
| s390x | STIDP and facility list | Facility bits and machine configuration | Lowcore, SCLP and channel subsystem | arch, machine type, facilities, CPU address, interruption capabilities |
| Other Linux architectures | Architecture-specific processor ID/control registers as specified by the ISA and Linux port | Per-architecture feature discovery only; never probe undefined registers | Firmware tables / Device Tree and architecture controller drivers | Stable architecture ID, raw vendor/part/revision, feature bitmap, topology and controller identifiers |

Detection is a two-stage operation: identify the ISA and CPU safely first, then enumerate optional features and platform interrupt controllers. A missing identification register or optional extension must be represented as **unknown/not present**, never guessed. Feature use requires both hardware support and kernel save/restore/context support.

## Interrupt, syscall and CPU backend implementation inventory

| Layer | x86_64 current evidence | Required architecture-neutral interface | Per-architecture implementation still required |
|---|---|---|---|
| CPU identification | Earlier Koronos work records CPUID vendor/family/model/stepping, address widths, features and topology; re-audit the current branch before relying on it | `cpu_identify()`, `cpu_features()`, `cpu_topology()` | CPUID backend; MIDR/ID-register backend; RISC-V CSR/SBI backend; PVR/STIDP/PRId backends |
| Exception frame | x86_64 assembly frame layout and typed dispatcher frame work exists | `arch_trap_frame`, `arch_decode_trap()` | Register save/restore layouts and error-code semantics for each ISA |
| Interrupt controller | x86 IDT/APIC path is the current development target | `irq_domain`, `irq_register()`, `irq_eoi()`, `irq_mask()` | PIC/APIC, GIC, PLIC/APLIC+IMSIC, XICS/XIVE, MIPS/SoC and other controllers |
| Syscall entry | x86_64 INT 0x80 acknowledgement is present in current candidate work; full syscall-to-VFS/process path is not accepted | `arch_syscall_enter()`, common validated dispatcher, `arch_syscall_return()` | SYSCALL/SYSRET, SVC/ERET, ECALL/SRET, SC/return, trap/gateway backends |
| Syscall ABI | Koronos syscall IDs are its own ABI; Linux numbers are reference data only | Generated per-ABI syscall metadata + common semantic handlers | Register mapping, compat ABI, argument validation and return/error translation per architecture |
| Per-CPU state | BSP identity/TSS foundations exist in x86_64 work; AP startup and real SMP remain unverified | `cpu_local`, per-CPU interrupt stack, scheduler state, syscall stack | Per-CPU exception stacks, TSS or equivalent, local timer and IPI support |
| Context switch / SMP | Scheduler parallel API remains fail-closed until AP workers and real overlap are proven | `arch_context_switch()`, `arch_send_ipi()`, `arch_tlb_shootdown()` | ABI-preserving context switch, AP/hart startup, timer preemption, IPI and TLB shootdown |
| Boot / MMU | Native Koronos work is x86_64/Multiboot2-oriented | `arch_boot_parse()`, `mmu_ops`, `cache_ops` | Firmware entry, page-table format, TLB maintenance, cache coherency and relocation per ISA |

## Linux and XNU reference workflow

1. **Select an architecture port.** Start with Linux `arch/<arch>/`, its Kconfig, Makefile, boot protocol, entry assembly, interrupt controller drivers, timer, SMP and UAPI syscall definitions.
2. **Read the normative specification.** Confirm instruction semantics, privilege transitions, exception frame, memory model, MMU and interrupt-controller behavior against the ISA/platform specification.
3. **Separate entry assembly from common policy.** Save the complete architectural state, establish a trusted per-CPU stack, validate origin/privilege and only then enter common C/C++ code. Keep fragile entry/exit code non-instrumentable.
4. **Use one Koronos semantic syscall layer.** Architecture stubs translate registers and calling conventions into the same validated internal syscall request. The VFS, process, permissions and error semantics must not be duplicated per ISA.
5. **Build one architecture backend at a time.** Add cross-toolchain, linker script, boot protocol, exception tests, syscall ABI tests, timer/interrupt tests, context-switch tests and QEMU (or board) smoke tests.
6. **Use XNU only where applicable.** Compare `osfmk/`, machine-dependent architecture code, Mach traps, BSD syscall glue and IOKit/platform drivers for x86_64 and arm64. XNU is not a reference implementation for the other Linux architectures.
7. **Record evidence per exact CPU/board and commit.** A compile-only or emulator-only result is not physical hardware support. Record emulator model, CPU features, firmware, kernel SHA, test logs and known omissions.

## Release and support labels

- **Implemented:** code exists in the current branch, is wired into the boot/runtime path, and has architecture-specific tests.
- **Partial:** some primitives exist, but a required runtime path or acceptance test is missing.
- **Reference-only:** architecture/ABI is catalogued; no native Koronos support claim.
- **Unsupported:** explicitly excluded from the current build.
- **Unknown:** not probed or evidence unavailable.

No architecture may be marked supported solely because CPU identification succeeded. Production support additionally requires a real boot, exception/IRQ delivery, timer, syscall round-trip from user mode, process lifecycle, storage/VFS, and SMP evidence where the platform claims SMP. Keep native-init exit 78 and all existing release gates fail-closed.

## Primary references

- Linux architecture documentation: https://docs.kernel.org/arch/
- Linux exception, interrupt, syscall and KVM entry/exit rules: https://docs.kernel.org/core-api/entry.html
- Linux x86 documentation: https://docs.kernel.org/arch/x86/
- Linux arm64 documentation: https://docs.kernel.org/arch/arm64/
- Linux RISC-V documentation: https://docs.kernel.org/arch/riscv/
- Linux PowerPC documentation: https://docs.kernel.org/arch/powerpc/
- Apple XNU source and supported architecture overview: https://github.com/apple-oss-distributions/xnu
- Linux syscall tables/UAPI: use the matching kernel source tree's `arch/<arch>/entry/syscalls/`, `arch/<arch>/include/uapi/` and generated syscall headers as the versioned authority.

## Current acceptance boundary (2026-11-04)

The current repositories are x86_64-centric. The latest native handoff commits report six target × firmware candidate cases, but those probes do not prove every CPU architecture in this matrix, native VFS completeness, real AP startup/SMP or production release acceptance. This matrix does not change the release gate or turn candidate evidence into a release claim.
