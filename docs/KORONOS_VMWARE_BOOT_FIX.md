# Koronos VMware boot stall fix

## Observed failure

VMware reached:

- `KORONOS READY`
- `Console fallback: VGA text + COM1`
- `Starting/Entering scheduler...`

and produced no further progress.

## Root cause

The x86-64 entry path calls `koronos_idle_loop` after `koronos_boot`. The previous implementation of `koronos_idle_loop` was an unconditional architecture `pause`/`yield` loop. No scheduler work was pumped and no liveness indication was emitted. Consequently, the VM looked stalled immediately after the scheduler handoff.

## Fix

`kernel/core/runtime_loop.cpp` now owns `koronos_idle_loop` and:

1. calls `chimera_sched_run_once(0)` on every iteration;
2. emits a VGA liveness heartbeat on row 25 every 0x100000 iterations;
3. uses `pause` on x86, `yield` on AArch64 and `nop` on RISC-V/generic targets;
4. avoids an early interrupt/HLT dependency until the timer/APIC service is initialized.

`kernel/core/arch_init.cpp` no longer contains a duplicate permanent idle loop. The VMware compatibility path retains detected logical CPU information without introducing an early SMP barrier.

`kernel/build-koronos.sh` now compiles and links `runtime_loop.cpp` and verifies the resulting image is ELF64 and exports `koronos_idle_loop`.

## Expected VMware behavior

After rebuilding the ISO and booting it, the final console line should become:

`Starting cooperative scheduler runtime...`

followed by a visible `KORONOS SCHEDULER ALIVE` heartbeat on the bottom VGA row. This proves the bootstrap vCPU is executing the scheduler pump rather than sitting in the former dead idle loop.

## Verification

The changed runtime and architecture units have been syntax/compile checked with the same freestanding flags used by the Koronos build. A complete ISO/VMware boot test must still be run on a machine with the ChimeraIIOS build environment and VMware available.
