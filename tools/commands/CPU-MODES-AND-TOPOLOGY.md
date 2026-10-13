# CPU execution profiles and processor topology

The `chimera-cpu-mode` command provides explicit user selection for supported DOS
emulation profiles and guest CPU topology.

- `chimera-cpu-mode --mode real --program GAME.EXE`: DOSBox/DOSBox-X with DPMI
  disabled; appropriate only for DOS software that does not require DPMI.
- `chimera-cpu-mode --mode protected --program APP.EXE`: DOSBox-X with DPMI enabled,
  allowing compatible DOS applications to request protected-mode execution. This is
  a **protected-capable** profile, not a guarantee that the program will enter or
  remain in protected mode. The application decides whether to use DPMI.
- `chimera-cpu-mode --qemu-iso path/to/chimera.iso --vcpus all --host-affinity`:
  starts an x86-64 QEMU guest with one virtual CPU per CPU available to the current
  process, and optionally pins the QEMU process to those host CPUs. Use `--list-cpus`
  to inspect the process's allowed host CPU set. `--vcpus N` chooses a positive count.

Examples:

```sh
chimera-cpu-mode --list-cpus
chimera-cpu-mode --mode real --program /games/OLDGAME.COM
chimera-cpu-mode --mode protected --program /apps/LEGACY.EXE
chimera-cpu-mode --qemu-iso build/ChimeraIIOS.iso --vcpus all --host-affinity
```

## Hardware mode boundary

On x86, real-address mode and protected mode are CPU architectural execution states,
not a normal per-application host setting. A running 64-bit OS cannot safely toggle
the physical processor into real mode while continuing to run itself. Switching mode
requires privileged boot/kernel code, descriptor tables, interrupt handling, and
careful transitions; protected-mode software can instead virtualize legacy execution.
The DOS profile above controls DPMI availability inside the guest emulator, while
QEMU runs a separate guest and offers a configurable virtual CPU topology.

The `--qemu-iso` option selects the number of guest vCPUs and optional host affinity;
it does not claim that Koronos starts or schedules every vCPU. Bare-metal genuine SMP
still requires AP startup, per-CPU scheduler state, inter-processor interrupts, and
concurrent execution evidence. Do not equate `-smp N` with proof of kernel SMP.

See Intel's [IA-32 / Intel 64 Software Developer Manuals](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)
for the architectural definition and mode-switch requirements.
