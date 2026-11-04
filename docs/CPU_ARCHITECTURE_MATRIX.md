# Koronos CPU architecture, interrupt and syscall matrix

**Schema:** `KORONOS-CPU-ARCH-MATRIX-1`  
**Inventory source:** `isa/isa_database.json` (2026.10.11; 104 architecture identifiers)  
**Scope:** All inventory identifiers are represented. This includes physical CPU/MCU/DSP ISAs, aliases, extensions, GPUs and virtual ISAs. A row is not proof of an OS port, executable backend, or supported hardware. CISC/RISC labels are descriptive; some architectures are hybrid, VLIW, EPIC, DSP, GPU or virtual ISAs.

## Support boundary

| Layer | Current status |
|---|---|
| Native Koronos build | x86-64 |
| Additional detector branches | AArch64 and RV64 compile-time classification only; no bootable native pipeline |
| x86 CPU identity/features | CPUID vendor/model, basic features and topology leaves 0x1F/0x0B; AMD extended topology fallback |
| ACPI CPU discovery | MADT Local APIC and x2APIC entry parser; runtime ACPI root-table discovery still outstanding |
| x86 interrupt/syscall | IDT and DPL3 INT 0x80 foundation; AP startup, full interrupt-controller integration and complete process scheduler remain outstanding |
| Other ISA interrupt/syscall backends | Not implemented |
| SMP | CPU inventory is not online CPU state; AP INIT/SIPI and measured overlap are outstanding |

## Architecture family summary

| Family / class | Inventory identifiers | Linux reference | macOS / XNU | Koronos |
|---|---:|---|---|---|
| x86 CISC (16/32/64) | x86-16, x86-32, x86-64 | Linux x86 entry, IDT/APIC, SYSCALL/SYSENTER/INT 0x80 | Intel x86_64 on supported Intel Macs; 32-bit is historical | x86-64 build only |
| Arm RISC (AArch32/AArch64) | arm32, arm32-thumb, armv7-risc, armv7-m, armv8-a32, armv9-a64, aarch64 | Linux ARM exception vectors, GIC and SVC | arm64 Apple silicon only | AArch64 detection branch; no native image |
| RISC-V | riscv32, riscv64, riscv32e, riscv64e, riscv64gc, riscv128 | ECALL, S-mode traps, PLIC/APLIC/IMSIC by platform | Not supported | RV64 detection branch; no native image |
| Power ISA | powerpc, ppc64, power10, power10-mma | SC, exception vectors, MPIC/XICS/XIVE | Not supported | Inventory only |
| MIPS | mips32, mips64, mips16, mips64r6 | SYSCALL, CP0 exceptions | Not supported | Inventory only |
| IBM Z / s390 | s390x, ibm-z, ibm-s360 | SVC and lowcore interruption model | Not supported | Inventory only |
| LoongArch | loongarch32, loongarch64 | SYSCALL, exception vectors, EIOINTC/HTVEC | Not supported | Inventory only |
| SPARC | sparc-v8, sparc-v9 | Trap table, PIL, T 0x10 / T 0x6d | Not supported | Inventory only |
| m68k / Alpha / PA-RISC / SH / Xtensa / ARC / OpenRISC / Nios II / MicroBlaze / others | See machine-readable matrix | Linux architecture ports and legacy ABI details vary by architecture and kernel release | Not supported | Inventory only |
| MCU / embedded CISC/RISC | 8051, AVR, Z80, 6502, 8080, PDP-11, PIC, MSP430, 680x and related rows | Generally no standard Linux syscall ABI; Linux ports are not implied | Not supported | Inventory only |
| EPIC / VLIW / DSP | IA-64, E2K, C6000, Blackfin, Hexagon, dsPIC and related rows | Architecture-/vendor-specific or legacy | Not supported | Inventory only |
| GPU / VM ISAs | AMD/NVIDIA/Intel/Apple GPU, eBPF, WebAssembly, SPIR-V | Accelerator/VM interfaces, not general CPU syscall ABIs | Not macOS kernel CPU architectures | Catalog only |

## Linux syscall ABI reference table

The entry instruction and register convention are architecture-specific. These are Linux user/kernel ABI references, not Koronos ABI promises.

| Linux architecture | Entry | Syscall number | Arguments | Return |
|---|---|---|---|---|
| x86-64 | `syscall` | rax | rdi,rsi,rdx,r10,r8,r9 | rax |
| i386 | `int 0x80` / `sysenter` | eax | ebx,ecx,edx,esi,edi,ebp | eax |
| AArch64 | `svc #0` | w8 | x0-x5 | x0 |
| ARM EABI | `svc #0` | r7 | r0-r6 | r0 |
| RISC-V | `ecall` | a7 | a0-a5 | a0 |
| MIPS | `syscall` | v0 | a0-a5 | v0 |
| PowerPC | `sc` | r0 | r3-r8 | r3 |
| s390/s390x | `svc 0` | r1 | r2-r7 | r2 |
| LoongArch | `syscall 0` | a7 | a0-a5 | a0 |
| m68k | `trap #0` | d0 | d1-d5 | d0 |
| SPARC32/64 | `t 0x10` / `t 0x6d` | g1 | o0-o5 | o0 |
| Alpha | `callsys` | v0 | a0-a5 | v0 |
| PA-RISC | `ble` gateway | r20 | ABI-specific | r28 |
| SuperH | `trapa #31` | r3 | ABI-specific | r0 |
| ARC | `trap0` | r8 | ABI-specific | r0 |
| Xtensa | configuration-specific syscall trap | a2 | ABI-specific | a2 |
| Nios II | `trap` | r2 | ABI-specific | r2 |
| MicroBlaze | `brki` | r12 | ABI-specific | r3 |
| OpenRISC | `l.trap` | ABI-specific | ABI-specific | ABI-specific |

## Interrupt architecture reference

| ISA family | Synchronous exceptions / syscall | Asynchronous interrupt controller model |
|---|---|---|
| x86 | IDT exception/trap gates; SYSCALL MSRs or INT gate | Local APIC/x2APIC, IOAPIC, MSI/MSI-X; legacy PIC where required |
| AArch64 | EL1/EL2 exception vector table; SVC | GICv2/v3/v4, virtual interrupts, architectural timer |
| ARM A/R | ARM exception vectors; SVC; IRQ/FIQ | GIC or SoC-specific VIC |
| RISC-V | stvec/sepc/scause; ECALL; delegation | PLIC or APLIC+IMSIC; local timer/software interrupts |
| MIPS | CP0 exception state and vectors; SYSCALL | SoC interrupt controller, optional GIC |
| Power | exception vectors; SC | MPIC, XICS or XIVE; decrementer |
| s390x | program/interruption state and SVC | External, I/O, machine-check and restart interruptions via lowcore |
| LoongArch | exception entry and CSR state; SYSCALL | EIOINTC/HTVEC and per-CPU interrupt routing |
| SPARC | trap table and trap-level state | PIL levels and platform interrupt controller |
| m68k | vector table; TRAP | autovector interrupt levels |
| Alpha | PALcode exception entry; CALLSYS | PALcode/platform interrupt handling |
| Embedded MCU | ISA-specific vector/trap model | Device-specific interrupt controller and priority scheme |

## macOS / XNU comparison

Apple documents macOS development for Intel-based Macs and Apple silicon, and documents universal `x86_64` + `arm64` binaries. The kernel-facing architecture boundary is therefore limited to those two families; this is not a promise that every Intel CPU generation remains supported by every macOS release.

| Area | Intel macOS | Apple silicon macOS | Koronos design implication |
|---|---|---|---|
| ISA | x86-64 | AArch64/arm64 | Keep architecture-specific entry/interrupt backends separate |
| Exception/interrupt entry | x86 IDT/APIC model | Arm exception levels/vector tables and platform interrupt controller | Never reuse x86 IDT assumptions on Arm |
| Syscall transition | x86-64 `syscall` | Arm SVC exception path | Separate trap frame, register ABI and syscall entry implementation |
| CPU feature discovery | CPUID and OS-provided feature interfaces | CPU/system feature interfaces and Arm feature registers | Discover features dynamically; avoid fixed CPU/page/cache assumptions |
| Binary portability | x86_64 | arm64; universal binaries contain both slices | Build artifacts and kernel images remain architecture-specific |

The Darwin syscall ABI is distinct from Linux and is not a stable third-party kernel ABI. Do not copy Linux syscall numbers or assume Darwin's syscall table is interchangeable.

## Table-driven detection contract

1. Detect the executing ISA family using the architecture-defined mechanism: CPUID on x86; ID registers on Arm; `mvendorid`, `marchid`, `mimpid` and extension discovery on RISC-V; firmware/SoC descriptions where the ISA has no universal discovery mechanism.
2. Match the normalized architecture ID to the inventory row. A match returns only the ISA descriptor and reference metadata.
3. Probe model/vendor/features separately. A family match is not a CPU model match, and instruction-set extensions must be enabled only after runtime feature and OS-state checks.
4. Discover topology independently: CPUID topology leaves or ACPI MADT on x86; ACPI PPTT/ MADT or Device Tree on Arm; platform/firmware topology on RISC-V and other systems.
5. Keep discovered CPUs distinct from scheduler-online CPUs. Only successful AP/secondary-core startup and online acknowledgement can increase online count.
6. Keep per-architecture syscall and interrupt backends explicit. An inventory row must never auto-enable an unimplemented backend.

## Per-architecture details

The machine-readable file `data/isa/cpu_architecture_matrix.json` contains one row for every ISA database architecture identifier, including syscall entry/registers, interrupt model, Linux reference status, macOS status, Koronos implementation status, detection method and original ISA inventory status. Unsupported or unverified details are explicitly marked rather than inferred.

## Reference sources

- Linux architecture documentation: https://docs.kernel.org/arch/
- Linux architecture syscall calling conventions: https://man.archlinux.org/man/syscall.2
- Linux kernel architecture documentation index: https://cdn.kernel.org/doc/html/latest/
- Linux Arm ACPI / Device Tree discovery: https://www.kernel.org/doc/html/latest/arch/arm64/arm-acpi.html
- Apple architecture differences: https://developer.apple.com/documentation/apple-silicon/addressing-architectural-differences-in-your-macos-code
- Apple Intel/Apple silicon porting: https://developer.apple.com/documentation/Apple-Silicon/porting-your-macos-apps-to-apple-silicon
- Apple universal binaries: https://developer.apple.com/documentation/apple-silicon/building-a-universal-macos-binary
- RISC-V ISA specifications: https://docs.riscv.org/reference/isa/
- Arm architecture documentation: https://developer.arm.com/architectures
- Intel Software Developer Manuals: https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html

Linux syscall table source is a quick convention reference; for implementation, pin the exact Linux kernel release and inspect its `arch/<arch>/entry`, syscall table, exception and interrupt-controller code. Apple public porting documentation is not a substitute for XNU source inspection or platform documentation.
