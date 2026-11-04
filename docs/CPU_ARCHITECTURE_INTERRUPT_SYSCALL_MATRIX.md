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
| CISC | x86_64: Intel/AMD 64-bit, compatible CPUs | IDT gates; CPU exception frames; local APIC / IO-APIC or x2APIC; NMI and local timer paths | `SYSCALL`; number EAX; args RDI, RSI, RDX, R10, R8, R9; result RAX; `SYSRETQ`/IRET return paths | **Partial / experimental**: x86-64 boot and IDT exception frame code exists; current hardware IRQ implementation uses legacy PIC/PIT. CPUID detection is implemented with decoded family/model/stepping, feature bitmap, XCR0 and address widths. A DPL3 INT 0x80 acknowledgement path exists; full APIC routing, process-owned fd/VFS syscalls and production lifecycle remain separate gates. | XNU has x86_64 machine-dependent trap/interrupt and BSD/Mach syscall paths. Compare source; do not copy private syscall numbers. |
| CISC | i386: Intel/AMD 32-bit x86 | IDT; PIC or APIC; privilege transitions via interrupt/trap gates | `int 0x80` or `SYSENTER`; number EAX; args EBX, ECX, EDX, ESI, EDI, EBP; result EAX | **Reference-only**: no 32-bit Koronos boot/entry backend verified | Historical XNU x86 support is not a current i386 target |
| CISC | m68k: Motorola 680x0 | Vector table, synchronous traps and autovectors; platform interrupt controller | `trap #0`; Linux ABI uses D0 for number and architecture-defined data/address registers for arguments | **Reference-only** | No XNU backend |
| CISC | s390x / s390: IBM Z | Program, supervisor-call, external and I/O interruption classes; lowcore interruption state | `svc`; Linux ABI is architecture-specific (SVC number/register convention); use the kernel syscall table and ABI headers as authority | **Reference-only** | No XNU backend |
| CISC | Alpha: DEC Alpha | PALcode-assisted exception/interrupt entry and processor-specific vectors | `callsys`; V0 syscall number; A0-A5 arguments; architecture-defined error/result convention | **Reference-only** | No XNU backend |
| RISC | arm64 / AArch64: Arm Cortex-A, Neoverse, Apple Silicon | Exception-level vector table; synchronous exceptions, IRQ/FIQ; GICv2/v3/v4 or platform controller | `SVC #0`; W8 number; X0-X5 arguments; X0 result; EL0↔EL1 transition | **Port skeleton / partial detector**: MIDR_EL1, MPIDR_EL1 and selected ID_AA64 registers are read by the detector; entry.S/priv.S are skeletons. No complete vector table, GIC, SVC, timer, PSCI, context-switch or boot acceptance | XNU supports arm64 and uses its own machine-dependent exception and Mach/BSD syscall layers. Apple Silicon belongs here; it is not x86. |
| RISC | arm / AArch32: Cortex-A/R and supported SoCs | Vector table; IRQ/FIQ; GIC or SoC interrupt controller; exception modes | `SVC`; EABI uses R7 number, R0-R6 arguments, R0 result (ABI variants must be explicit) | **Reference-only** | No current XNU 32-bit ARM target |
| RISC | riscv64 / riscv32: RV64/RV32 implementations | `stvec` trap entry; supervisor exceptions/interrupts; SBI firmware boundary; PLIC or APLIC+IMSIC depending on platform | `ecall`; A7 number; A0-A5 arguments; A0 result | **Port skeleton / partial detector**: RV64 entry/privilege stubs exist and XLEN is identified at compile time. FDT/ACPI and SBI discovery, stvec dispatcher, timer, PLIC/APLIC+IMSIC, ECALL/SRET and boot acceptance are not implemented | No XNU backend |
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


## Source-backed implementation update

The machine-readable target registry is `kernel/arch/targets.json`; the per-architecture detection and ABI registry is `data/cpu-architecture-matrix.json`.

- **x86_64:** `kernel/core/arch_init.cpp` now normalizes CPUID vendor, family, model, stepping, brand, topology/APIC ID, address widths, feature bits and XCR0. AVX is exposed only when OSXSAVE and XCR0 state permit it. The current interrupt backend remains IDT plus legacy PIC/PIT; APIC routing is not claimed complete.
- **AArch64:** the detector reads MIDR_EL1, MPIDR_EL1 and ID_AA64PFR0/MMFR0/ISAR0. PARange is decoded instead of being mislabeled as a byte width. Raw ID registers are stored separately from normalized feature flags. The vector/GIC/SVC/timer/PSCI/context-switch implementation remains incomplete.
- **RISC-V64:** XLEN is identified at compile time. The code deliberately avoids reading M-mode-only CSRs after OpenSBI enters supervisor mode. FDT/ACPI and SBI discovery remain required; the existing assembly files are entry/privilege skeletons, not a complete trap/syscall backend.
- **Host regression:** `tests/kernel/run-cpu-profile-host-tests.sh` compiles and executes the CPUID profile test; the Koronos build invokes it before linking.

A detector result is not proof of a native backend. Topology count is not an online-CPU count; AP/hart startup acknowledgements and concurrent execution are required for SMP claims.


## Exact Linux syscall register ABI matrix

The table below records the Linux *calling convention*, not Linux syscall numbers. Number tables change with kernel versions and ABI variants; use the target kernel's syscall table/UAPI as the versioned source of syscall numbers. Koronos syscall IDs remain its own stable semantic ABI and must never be copied from Linux.

| ISA / ABI | Trap instruction / entry | Syscall number register | Argument registers | Return and error convention |
|---|---|---|---|---|
| x86_64 | `syscall` | EAX | RDI, RSI, RDX, R10, R8, R9 | RAX; negative errno |
| i386 | `int $0x80` | EAX | EBX, ECX, EDX, ESI, EDI, EBP | EAX; EDX is secondary return |
| m68k | `trap #0` | D0 | D1, D2, D3, D4, D5, A0 | D0 |
| s390x | `svc 0` | R1 | R2, R3, R4, R5, R6, R7 | R2; R3 secondary return |
| Alpha | `callsys` | V0 | A0, A1, A2, A3, A4, A5 | V0; A4 secondary return; A3 error flag |
| ARM64 | `svc #0` | W8 | X0, X1, X2, X3, X4, X5 | X0; X1 secondary return |
| ARM EABI | `swi 0x0` | R7 | R0, R1, R2, R3, R4, R5, R6 | R0; R1 secondary return |
| RISC-V 64 | `ecall` | A7 | A0, A1, A2, A3, A4, A5 | A0; A1 secondary return |
| RISC-V 32 | `ecall` | A7 | A0, A1, A2, A3, A4, A5 | A0; A1 secondary return |
| PowerPC64 | `sc` | R0 | R3, R4, R5, R6, R7, R8 | R3; CR0.SO indicates error |
| MIPS n32/n64 | `syscall` | V0 | A0, A1, A2, A3, A4, A5 | V0; V1 secondary return; A3 error flag |
| MIPS o32 | `syscall` | V0 | A0, A1, A2, A3; arguments 5–8 on user stack | V0; V1 secondary return; A3 error flag |
| SPARC64 | `t 0x6d` | G1 | O0, O1, O2, O3, O4, O5 | O0; O1 secondary return; PSR/CSR carry signals error |
| LoongArch64 | `syscall 0` | A7 | A0, A1, A2, A3, A4, A5, A6 | A0 |
| ARC | `trap0` | R8 | R0, R1, R2, R3, R4, R5 | R0 |
| OpenRISC | `l.sys` syscall exception path | R11 | R3, R4, R5, R6, R7, R8 | R11 |
| PA-RISC | `ble 0x100(%sr2,%r0)` | R20 | R26, R25, R24, R23, R22, R21 | R28 |
| Nios II | `trap` | R2 | R4, R5, R6, R7, R8, R9 | R2; R7 error flag |
| MicroBlaze | `brki r14,8` | R12 | R5, R6, R7, R8, R9, R10 | R3 |
| Xtensa | `syscall` | A2 | A6, A3, A4, A5, A8, A9 | A2 |
| SuperH | `trapa #31` | R3 | R4, R5, R6, R7, R0, R1, R2 | R0; R1 secondary return |
| C-SKY | TRAP0 syscall entry | `syscallid` special register | A0-A3; ABI v1 uses R6/R7 for args 5/6; ABI v2 uses R4/R5 | A0; ABI-version-specific |
| Hexagon | `trap0 #1` | R6 | R0, R1, R2, R3, R4, R5 | R0 |

The Linux man-pages calling-convention reference documents the standard register tables and warns that ABI-specific argument alignment and clobber rules matter. C-SKY, Hexagon and OpenRISC details above are checked against their Linux architecture entry sources. Do not infer a convention for an architecture from another ISA family.

### Reference source map

- Linux syscall calling conventions: https://man7.org/linux/man-pages/man2/syscall.2.html
- Linux exception/interrupt/syscall entry ordering and `noinstr` constraints: https://docs.kernel.org/core-api/entry.html
- Linux architecture-specific source and boot/CPU feature documentation: https://docs.kernel.org/arch/
- Linux generic syscall-table workflow: https://docs.kernel.org/process/adding-syscalls.html
- Linux C-SKY entry source: https://github.com/torvalds/linux/blob/master/arch/csky/kernel/entry.S
- Linux Hexagon trap/syscall source: https://github.com/torvalds/linux/blob/master/arch/hexagon/kernel/traps.c
- Linux OpenRISC syscall entry source: https://github.com/torvalds/linux/blob/master/arch/openrisc/kernel/entry.S
- XNU ARM64 exception/SVC dispatch: https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/arm64/sleh.c
- XNU ARM64 bootstrap and per-CPU setup: https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/arm64/start.s
- XNU x86_64 IDT, trap, interrupt and syscall stubs: https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/x86_64/idt64.s

Linux's syscall table is the primary source for architecture ABI details. XNU is used as a comparative implementation reference only for its x86_64 and arm64 machine-dependent paths; it is not treated as a general RISC/CISC porting source.


## Runtime backend selection

CPU identification now feeds an in-kernel architecture dispatch registry rather than leaving the matrix as documentation alone:

- `kernel/core/arch_init.cpp` normalizes the detected architecture and queries `koronos_arch_backend_lookup()`.
- `kernel/core/arch_backend.cpp` contains 22 unique runtime backend descriptors. Each descriptor reports the ISA family, maturity, presence of an entry stub, interrupt backend and syscall backend, and the applicable trap/IRQ model.
- `koronos_cpu_features` reports the selected backend status and which backend layers are actually present.
- `tests/kernel/cpu_profile_host_test.cpp` verifies that all 22 IDs are unique, that every descriptor has explicit interrupt/syscall metadata, and that the detected CPU selects the matching descriptor.
- `kernel/build-koronos.sh` compiles the registry and runs the host regression before linking the native x86_64 kernel.

The runtime registry intentionally returns **partial** for x86_64, **port-skeleton** for AArch64 and RISC-V64, and **reference-only** for the remaining architectures. It does not dispatch into unimplemented backends. A port-skeleton entry stub is not a working interrupt controller, syscall path or bootable kernel.
