# Koronos boot-to-userspace gap audit against Linux v7.2.2

**Status:** source audit / gap inventory; not a claim of fixes or production acceptance.  
**Reference:** Linux v7.2.2 source tree, with the Bootlin browser endpoint blocked in this run. Linux paths below identify the corresponding implementation to compare; no Linux code is copied into Koronos.

## Executive result

The tracked native boot path is **x86_64 only**. `kernel/arch/targets.json` labels AArch64 and RISC-V as `port-layer`, not production-booted targets. The x86_32 entry is a separate legacy bring-up path. RegisterN/R8192/C8192 and ISA emulation are virtual/emulated targets, not additional native CPU ports. OctavianOS consumes the Chimera kernel source and its ISO payload contract currently declares `architecture: x86_64`.

The key end-to-end gap is not a single instruction or boot logo. Koronos needs a complete chain: firmware/boot protocol → architecture setup and memory map → physical/virtual memory → traps/interrupts and timer → real per-CPU startup → runnable scheduler → process address space and ELF execution → complete syscall/process lifecycle → mountable target rootfs and services → userspace readiness. A kernel build or module-routing smoke proves only a subset.

## Findings and Linux counterparts

| Priority | Koronos gap / evidence | Linux counterpart to compare | Required acceptance |
|---|---|---|---|
| P0 | **Architecture scope is overstated if every ISA is called bootable.** Current target registry marks x86_64 implemented, AArch64/RV64 port-layer, Cortex-M boot-port, and R8192/C8192 emulator. | `arch/*/Kconfig`, `arch/*/Makefile`, `Documentation/arch/`, architecture boot entry and linker scripts | Publish per-architecture status separately: native booted, compiled-only, port-layer, or emulator. Never reuse x86 ELF/ISO as proof of ARM/RISC-V boot. |
| P0 | **Entry/firmware handoff differs by architecture.** x86_64 builder assembles x86_64-only NASM sources. AArch64/RV64 have small `_start` stubs but are not linked by that builder. Their boot protocol, stack, exception level, DTB/FDT and hart/CPU arguments need validation. | `arch/x86/kernel/head_64.S`, `arch/arm64/kernel/head.S`, `arch/riscv/kernel/head.S`, `init/main.c` | Cross-build each declared target; boot under the correct firmware/boot protocol; retain entry registers, firmware data and first-console logs. |
| P0 | **Memory/ELF admission is not the same as a running init.** Existing audit records load-plan/admission modes; actual process-owned page tables, PT_LOAD+BSS, permission enforcement, user stack and address-space lifecycle must be verified on the real payload. | `mm/page_alloc.c`, `mm/vmalloc.c`, `mm/memory.c`, `fs/exec.c`, `fs/binfmt_elf.c`, `kernel/fork.c` | Run a production init ELF, validate mappings/relocations/BSS/stack and user permissions, and observe its first user-originated syscall. |
| P0 | **Syscall ABI is partial.** Current `kernel/core/syscall.cpp` implements GETPID, YIELD, TIME_TICKS and semantic EXIT acknowledgements; unsupported calls return ENOSYS. GETPID returns constant 1, and EXIT does not demonstrate teardown. | `arch/x86/entry/`, `kernel/entry/common.c`, `kernel/sys.c`, `kernel/exit.c`, `kernel/fork.c`, `kernel/time/` | Use process-owned PID; safe user-memory copy; defined errno/ABI; implement or explicitly reject each advertised syscall; test EXIT/reaping/wait, blocking I/O and timer wakeups from ring 3. |
| P0 | **Scheduler contract is not genuine SMP.** Scheduler code uses shared task tables and CPU indices; that alone does not prove hardware AP startup, per-CPU stacks/state, interrupt-driven preemption or race-free wakeups. | `kernel/sched/core.c`, `kernel/sched/fair.c`, `kernel/smp.c`, `arch/x86/kernel/smpboot.c`, `kernel/irq/` | QEMU SMP and physical evidence: AP online messages tied to APIC/hart IDs, concurrent per-CPU work, timer interrupts, affinity, cross-CPU wakeup and lock stress. |
| P1 | **Interrupt/timer and context-return path must be target-specific.** A scheduler yield call is not proof of preemption or a correct ring-3 return path. | `arch/x86/entry/entry_64.S`, `arch/arm64/kernel/entry.S`, `arch/riscv/kernel/entry.S`, `kernel/time/timer.c` | Exception/syscall frame round-trip tests; IRQ-safe locks; timer-driven preemption and sleep/wakeup tests per architecture. |
| P0 | **Initramfs/rootfs formats and target modules must agree.** The ISO contract expects distinct Live, Installer and Recovery payloads; compressed archive format, module names, manifest and loader parser must agree end-to-end. | `init/initramfs.c`, `lib/decompress_*.c`, `fs/exec.c`, `init/main.c` | Extract each actual ISO payload; validate checksum, compression, archive records, paths and ELF machine; boot each target and prove selected init executed. |
| P0 | **Userspace service chain is incomplete/unproven after ring-3 entry.** A smoke ELF or kernel message cannot prove VFS, device services, session manager, installer/recovery shell or desktop. | `init/main.c`, `kernel/kthread.c`, `fs/`, `drivers/base/`, `drivers/tty/` | Target-specific service dependency graph reaches a shell/session; only the real init emits `USERSPACE READY: target=<target> init_pid=<nonzero>`. |
| P1 | **Device/console availability and fallback must be explicit.** Boot artwork and framebuffer files are not display-driver proof; early console must work when graphics fails. | `drivers/tty/serial/`, `drivers/video/`, `drivers/base/`, `kernel/printk/` | Serial/debug console plus VGA/framebuffer fallback; enumerate display/storage/input devices and report optional driver failures without hanging. |
| P1 | **CPU feature/topology probing is descriptive until tied to safe execution.** Target registry lists CPUID/APIC/NX/SSE2 etc.; wide RegisterN profiles are emulation/context metadata, not hardware ISA support. | `arch/x86/kernel/cpu/`, `arch/x86/kernel/smpboot.c`, `kernel/cpu.c` | Gate instructions on probed features; record topology; unsupported feature tests fail safely; do not report virtual 8192-bit ISA as native CPU execution. |

## Architecture matrix (current evidence)

| Architecture / profile | Current tracked status | Main missing evidence |
|---|---|---|
| x86_64 | Native build/ISO path; production userspace acceptance still blocked | Six real target × firmware boots; process init, services, desktop handoff, AP-backed SMP |
| x86_32 | Separate legacy bring-up code | Independently reproducible boot, memory/interrupt/process/user-init acceptance |
| AArch64 | Port layer | Architecture-specific builder/linker, EL setup, exception vectors, MMU, PSCI/SMP, init execution |
| RISC-V RV64 | Port layer | SBI/FDT contract, trap vector, page tables, timer/IPI, hart bring-up, init execution |
| ARM Cortex-M | Boot-port / embedded scope | Explicit boot contract and standalone acceptance; not a Linux-style desktop target |
| R8192 / C8192 / RegisterN | Emulator/virtual ISA | Host/emulator conformance only; never label native CPU boot |
| OctavianOS | x86_64 ISO target contract | Same Koronos runtime gates; no independent ARM/RISC-V production kernel evidence |

## Required test ladder

1. **Static contracts:** target IDs, boot protocol, ELF machine/class, module names, archive/compression format, manifest hashes.
2. **Build:** clean cross-build for each architecture claimed as compiled; no architecture status inferred from x86_64 build.
3. **Boot entry:** serial/debug trace and CPU/firmware identity for each supported architecture.
4. **Kernel services:** memory allocator, exception handling, timer interrupts, scheduler, device/console and VFS tests.
5. **User process:** production ELF loads into isolated address space; ring-3 syscall originates from that process; PID is allocated, not hard-coded.
6. **Target services:** Live Aurora/Marine, Installer, Recovery and Diagnostics each start their own real init and service graph.
7. **SMP:** per-CPU AP/hart online evidence plus concurrent execution and cross-CPU synchronization.
8. **Production matrix:** Live, Installer, Recovery × BIOS, UEFI (six x86_64 cases), with PASS/FAIL/NOT RUN and immutable logs. Do not generalize this matrix to other architectures.

## Fail-closed policy

A missing target-specific kernel, payload, init ELF, service, or test is **NOT RUN / NOT IMPLEMENTED**, not PASS. Do not publish ISO/release artifacts as production-ready until all required x86_64 acceptance cases pass. Other architectures remain unavailable until their own boot and userspace matrices pass.

## Reference source locations

- Linux v7.2.2 source browser requested: https://elixir.bootlin.com/linux/v7.2.2/source (blocked by robots in this research session)
- Linux x86 architecture setup: https://github.com/torvalds/linux/blob/master/arch/x86/kernel/setup.c
- Linux x86 memory initialization: https://github.com/torvalds/linux/blob/master/arch/x86/mm/init.c
- Linux x86 boot protocol docs: https://www.kernel.org/doc/html/v7.0-rc1/arch/x86/boot.html

The GitHub master links are navigation aids, not version-pinned v7.2.2 evidence. Confirm exact v7.2.2 source before using any implementation detail as a patch template.
