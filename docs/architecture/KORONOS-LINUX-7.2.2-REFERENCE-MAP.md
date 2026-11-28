# Koronos implementation map: Windows 2000 ASM and Linux v7.2.2

**Status:** reference map and implementation boundaries; not a claim of full Linux or Windows compatibility.

## Reference provenance

- User-supplied reference: `W2K-ASM Notepad.txt.pdf`, especially pages 248–261 (dispatcher/ready queues/context switch), 417–418 (system-service dispatch and user argument capture), and 472–474 (page-fault entry and access validation).
- Linux reference tag: `v7.2.2`, release commit `52c36105f76e` (2026-08-28). The supplied Bootlin URL is the preferred browser index, but automated retrieval is blocked by its robots policy in this environment. The source paths and blob IDs below are retained from the earlier source inspection; re-fetch and verify blobs before any future code port.
- Linux reference is GPL-2.0. This document records subsystem contracts and does not copy Linux implementation code. Any future source reuse must undergo license/provenance review and preserve applicable notices.
- External architecture references: [Linux kernel process/context-switch lecture](https://linux-kernel-labs.github.io/refs/heads/master/lectures/processes.html), [Wayland architecture](https://wayland.freedesktop.org/architecture.html), and [Wayland book architecture](https://wayland.freedesktop.org/docs/book/Architecture.html).

## Linux v7.2.2 source map

| Concern | Reference path | Previously recorded blob |
|---|---|---|
| Scheduler core, run queues, scheduling and context switch | `kernel/sched/core.c` | `96226707c2f6135341aa779b8262f113e103d8ad` |
| x86-64 syscall/interrupt entry | `arch/x86/entry/entry_64.S` | `253f0a585927fe8b18519dd560eb4e702f8c893d` |
| x86-64 task state and context | `arch/x86/kernel/process_64.c` | `d44afbe005bb512a8d1ad8a904c112559ff8596b` |
| x86 page-fault entry and policy | `arch/x86/mm/fault.c` | `45b99c3b1442d4f18a5179dd1773d76d60342bbb` |
| Generic page faults and VM | `mm/memory.c` | `6b8280cfc1dbea5f370efaeda0f100e2720e523d` |
| VFS path lookup | `fs/namei.c` | `19ce43c9a6e662da1a4dcdbc88bcd4ffec6c0c5b` |
| File read/write syscalls | `fs/read_write.c` | `e8c14e2760b20331ce0aeff15e24cefa2d7df886` |
| VFS contracts | `Documentation/filesystems/vfs.rst` | `7c753148af8883b4c09e5306ee79ef2bd65ebf8c` |

Additional files to inspect recursively before implementing their respective subsystems include `kernel/fork.c`, `kernel/exit.c`, `kernel/sched/fair.c`, `include/linux/sched.h`, `include/linux/fs.h`, `fs/open.c`, `fs/file_table.c`, `mm/mmap.c`, `mm/vmalloc.c`, `arch/x86/kernel/process.c`, `arch/x86/include/asm/switch_to.h`, and `init/main.c`.

## Cross-reference: Windows 2000 ASM

| W2K-ASM pages | Contract to study | Koronos/Linux analogue |
|---|---|---|
| 248–261 | Dispatcher lock discipline, ready-queue selection, stack/context handoff, address-space transition and FP state | `kernel/sched/core.c`, `arch/x86/kernel/process_64.c`, `arch/x86/entry/entry_64.S` |
| 417–418 | System-service table selection, bounds checks and safe capture of user arguments | `arch/x86/entry/entry_64.S`, `kernel/sys.c`, `fs/read_write.c` |
| 472–474 | Fault address capture, access type/privilege decode, VM resolution and user access violation | `arch/x86/mm/fault.c`, `mm/memory.c` |

Windows names and structures are useful for comparison only. Koronos should implement its own documented interfaces and must not copy proprietary Windows code.

## Additional Linux userspace and desktop source references

The following upstream source files were inspected as behavioral and architectural references. Their implementation code is not copied into Koronos.

| Subsystem | Upstream source | Recorded blob |
|---|---|---|
| PID 1 bootstrap and manager initialization | [systemd `src/core/main.c`](https://github.com/systemd/systemd/blob/main/src/core/main.c) | `9bba133cd71e82adc11897cb81b1451e6b027883` |
| Service lifecycle and restart state | [systemd `src/core/service.c`](https://github.com/systemd/systemd/blob/main/src/core/service.c) | `acae0de3e16bb576797ea509764d1e4fdc9abbc4` |
| Compositor/output/input lifecycle | [Weston `libweston/compositor.c`](https://github.com/intel/external-weston/blob/master/libweston/compositor.c) | `67b5d28303f088c8d8caa9378511d7d6501d22f2` |
| Desktop shell policy and surface roles | [Weston `desktop-shell/shell.c`](https://github.com/intel/external-weston/blob/master/desktop-shell/shell.c) | `ceb45c74db0e1ebc30f34b452d9548a46cd21e2b` |

These references define future Koronos work, not features already completed:
- PID 1 must own service state, dependencies, child reaping, restart policy, and shutdown sequencing.
- A native compositor must own display outputs, input devices, surface/buffer lifetimes, frame scheduling, and shell policy.
- Aurora, Marine Blue, FreeXP and FreeWin11 require real sessions backed by that compositor and the native graphics/input stack. Static wallpapers, profile builds and gallery previews are not desktop-session acceptance.

## Current source baseline and this change set

The current source already has:
- a specialized single-CPU kernel-task context-switch and PIT-preemption self-test in `kernel/core/preemptive_sched.cpp` and `kernel/arch/x86_64/interrupts.asm`;
- a separate callback scheduler in `kernel/core/scheduler.cpp`, still used by `kernel/core/thread.cpp`;
- ring-3 ELF admission and a single selected target-init continuation;
- a validated newc initramfs namespace plus bounded RAM-backed `/tmp`.

This change set adds one narrow Linux x86-64 userspace/VFS vertical slice:
1. Linux syscall 8 (`lseek`) maps to Koronos semantic syscall `CHM_SYS_SEEK`.
2. Open-file state distinguishes read permission from write permission. `O_RDWR|O_CREAT|O_EXCL` is accepted only for direct children of `/tmp`.
3. `lseek` supports `SEEK_SET`, `SEEK_CUR`, and `SEEK_END`, with signed-offset underflow and overflow checks.
4. The Live initramfs includes a deterministic `/etc/os-release`.
5. The native ring-3 Live init tests `open/read/close` on `/etc/os-release`, then performs a `/tmp` write/seek/read/close round trip **before** emitting its userspace-ready marker.
6. A BIOS/QEMU workflow step requires the exact built ISO to emit kernel preemption, both user-originated filesystem PASS markers, the target-matched userspace-ready marker and kernel PID1-active evidence; the same structured ISO is also run through the six-case BIOS/UEFI handoff matrix.
7. The AP startup self-test now explicitly clears shared state, sends its second SIPI only if the AP has not acknowledged online, and reports a one-logical-CPU skip distinctly from an SMP pass.

The QEMU test is intentionally scoped to one BIOS Live boot. It does not prove UEFI, Installer, Recovery, production SMP scheduling, persistent disk VFS, process creation/reaping, a supervised PID1, or graphical desktop sessions.

## Remaining implementation sequence

1. Replace callback-only thread dispatch with a process-independent kernel-thread context API, preserving interrupt state and lock ownership across context switches; test first-run, yield, timer preemption, block/wake, exit and stack reclamation.
2. Integrate process-owned saved contexts and address-space switching, including FS/GS/TLS, FPU/SIMD state, syscall return frames, fault delivery and parent/child wait/reap.
3. Integrate AP startup with per-CPU run queues, scheduler locks, reschedule IPIs, migration and measured simultaneous execution.
4. Replace the bounded initramfs-only descriptor table with a mount-aware VFS and block-backed persistent filesystem; prove data survives a reboot.
5. Make PID1 a kernel-scheduled supervisor with real child lifecycle and service restart policy.
6. Implement safe installer writes and post-reboot validation, plus recovery repair and an independently checked postcondition.
7. Implement and runtime-test the native Wayland-like compositor/display server, buffer exchange, input routing, GPU/software rendering and all four desktop sessions. Wayland architecture requires a compositor/display server that owns input and composition; a desktop wallpaper or static gallery is not a native session.
8. Run all six target/firmware combinations on one immutable ISO SHA-256 and require authenticated traces plus target-specific postconditions.

## Release rule

Never infer production readiness from source presence, unit tests, an ELF header, a static manifest, or a successful ISO packaging job. Production release remains blocked until all required runtime gates pass against the same ISO hash and the evidence verifier accepts the complete evidence bundle.
