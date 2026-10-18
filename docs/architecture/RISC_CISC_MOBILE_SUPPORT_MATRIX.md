# RISC/CISC and mobile portability contract

This matrix distinguishes **native OS support** from **emulating a CPU**. It is an acceptance policy, not a claim that every listed architecture currently boots.

## Current honest status

- **x86-64:** primary ISO target. CI has kernel-entry/QEMU smoke coverage and build checks; production Aurora, installation/reboot, recovery repair, and genuine SMP still require their separate acceptance evidence.
- **AArch64 and RISC-V 64:** mobile-microkernel source scaffolding exists. A source directory, cross-compiler, QEMU machine, or successful compile is not a working OS port.
- **x86 32-bit, ARMv7, RISC-V 32, MIPS, PowerPC, LoongArch, and other ISA families:** research/emulation targets until architecture-specific build and runtime evidence is attached.
- **Physical mobile devices:** each board/model requires a platform port, firmware/device-tree or ACPI support, drivers, power management, secure update and recovery. Generic QEMU tests cannot certify every phone or tablet.

The machine-readable contract is `architecture/support-matrix.json`. Its `release_supported` field remains false until the listed evidence is captured.

## Execution layers

1. **Native kernel:** matching boot protocol, CPU mode, page tables, interrupt controller, timer, scheduler/context switch, syscall ABI and exception paths.
2. **Virtual machine:** a declared QEMU/VM machine model and firmware, with the guest architecture matching the kernel.
3. **Instruction emulation:** a CPU emulator executes a guest ISA; it does not make a host kernel binary portable.
4. **Compatibility layer:** translates an OS or userspace ABI. This is separate from hardware/ISA emulation and from native boot.

## Required acceptance for each target

- Record target triple, compiler version, build flags, kernel format and machine/firmware profile.
- Cross-compile with warnings/errors retained; validate ELF class, endianness, machine ID, entry point and load segments.
- Boot the matching kernel under an architecture-appropriate emulator and capture serial logs.
- Require a **kernel boot marker**, then a separate **userspace-ready marker**, then target-specific service/UI readiness.
- Test interrupts, timers, memory permissions, user-mode transition, scheduler/context switch, storage and network drivers.
- For SMP, record CPU-online IDs and evidence of overlapping execution/per-CPU state. `-smp N` alone is not evidence.
- For mobile, additionally test display/touch/input, audio, Wi-Fi/cellular where supported, storage, suspend/resume, battery/power, verified updates and recovery.
- Publish only targets whose required evidence is attached to the release build.

## Safe fail-closed rules

- Never use an x86-64 kernel, initramfs or userspace payload for ARM/RISC-V.
- Do not advertise a target as supported from an ISA catalog entry, emulator catalog entry, source folder, menu item or successful compile.
- Unsupported target selection must produce a clear unavailable message and stop before loading an incompatible binary.
- Add new CPU families through a tested architecture port and a reproducible emulator/board profile; do not imply universal compatibility from a finite test matrix.

See also [Mobile Microkernel porting notes](../../Mobile%20Microkernel/docs/PORTING.md) and the emulator catalog workflow.
