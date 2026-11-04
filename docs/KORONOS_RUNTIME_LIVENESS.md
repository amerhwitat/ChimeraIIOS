# Koronos runtime liveness fix (2026-11-04)

## Symptoms reproduced

Two independent defects made a healthy kernel look stalled:

1. `make -C kernel` re-entered `defconfig`/`autoconf` forever and aborted with
   `make[...]: *** Deleting file '.../kernel/.config'`. GNU make treated the
   generated `.config` and `kor-obj.mk` as intermediate files (built by a rule
   with no prerequisites) and deleted them at the end of the run, so the next
   dispatch regenerated them again. With `-j2` two kconfig runs also raced on the
   same output file.
2. After bootstrap, every service task blocks (module registry empty, installers
   and live/recovery payloads not selected). The monitor printed a single
   snapshot and then blocked forever, so the scheduler loop had no runnable work
   and produced no further output — indistinguishable from a hang.

## Fix

- `kernel/Makefile`: `.PRECIOUS: $(CONFIG_FILE) $(OBJ_MK)` and `.NOTPARALLEL:`.
  Config generation is now single-pass and idempotent (`make` twice: no
  regeneration, no deletion, exit 0).
- `kernel/core/koronos.cpp`: the monitor task blocks after each snapshot; its id
  is exported as `koronos_monitor_task_id`.
- `kernel/core/runtime_loop.cpp`: when a dispatch finds no runnable task, the idle
  loop wakes the monitor every `0x00FFFFFF` spins. Each wake prints one snapshot,
  so runtime progress is observable instead of silent.

## Evidence (QEMU, BIOS, `-m 512 -smp 1`, 40 s capture)

Before: exactly one `[MON ]` snapshot, then silence; `runs=` frozen at 0/1.
After: 10 snapshots in 40 s, monitor `runs` incrementing (0 → 9), scheduler alive.

Both Chimera II OS (`kernel/`) and OctavianOS (vendored
`vendor/chimera-ii-os/source/kernel/`) carry the same fix; `make -C kernel check`
passes (ELF64, 4 boot banners).

Scope: this is scheduler liveness, not a userspace handoff. Kernel tasks still
block waiting for a real payload; `docs/PRODUCTION_USERSPACE_HANDOFF.md` remains
the gate for ring-3 execution.
