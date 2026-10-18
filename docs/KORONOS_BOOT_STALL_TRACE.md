# Koronos boot-stall trace (2026-10-13)

## Finding

The observed stall after `KORONOS READY` is a missing executable userspace handoff, not a slow driver scan. The kernel initializes its cooperative scheduler and submits one-shot bootstrap callbacks, then enters `koronos_idle_loop()`. Those callbacks register/report service state and block; no production path unpacks the Live initramfs, launches the installer UI, or enters ring 3. A scheduler heartbeat proves the kernel loop is alive, not that Live CD, installer, recovery, or Aurora is ready.

## Trace by boot target

| Stage/target | Current source behavior | Status |
| --- | --- | --- |
| Spit Fire / Jasper / GRUB | Menu configurations stage the Koronos ELF and selected Multiboot2 modules. | Menu/module staging only; not userspace readiness. |
| x86-64 entry | `kernel/arch/x86_64/entry.asm` builds identity paging with 2 MiB PDE flags `0x83`, enters long mode, and calls `koronos_boot`. | Supervisor-only bootstrap mapping; not a user address-space implementation. |
| Kernel init | `kernel/core/koronos.cpp::koronos_boot` probes CPU, firmware, PCI/device inventory, drivers, process admission and module registry. | Reaches `KORONOS READY`. |
| Scheduler | `kernel/core/runtime_loop.cpp::koronos_idle_loop` repeatedly calls `chimera_sched_run_once(0)`; task callbacks block after their bootstrap work. | Kernel loop can remain alive with zero runnable tasks; this is the observed idle/handoff stall. |
| Live CD | `task_live` previously called module acceptance a “Runtime handoff queued”. The initramfs is only a Multiboot2 data module; this kernel does not mount/unpack it or execute its init. | Not Live-userspace-ready; diagnostics now state this explicitly. |
| Installer | `task_installer` previously printed service/UI “started/initialized” messages before waiting for a nonexistent userspace loader. | No installer UI process is launched. Diagnostics now fail closed instead of claiming readiness. |
| Recovery | Jasper passes `chimera-recovery-initramfs` and `chimera-recovery-manifest`, but the module classifier previously returned `OTHER` for both. | Classifier now recognizes both module types; no recovery initramfs executor is implemented by this change. |
| Installed OS | The native installer UI and its disk-writing flow are not launched by Koronos. | No claim of disk installation, successful rootfs deployment, or first boot is made. |

## Root causes and remaining engineering gates

1. **No boot-wired ELF loader:** `kernel/core/process_loader.cpp` is a callback-based PT_LOAD/BSS/stack loader and host tests use a mock mapper. It is not wired to physical x86-64 user mappings or process entry.
2. **No user privilege transition:** the boot GDT has kernel code/data descriptors only; there is no production user GDT/TSS/IST setup, ring-3 iret frame, syscall entry/return path, or audited context switch connected to the admitted ELF.
3. **No initramfs executor:** module discovery stores physical module metadata but does not mount/unpack cpio/squashfs or invoke `/init`.
4. **Target service claims were ahead of reality:** registration/log messages did not mean the corresponding userspace service was running. The patched messages distinguish staged, blocked, and ready.
5. **No real SMP acceptance:** `chimera_sched_run_parallel` dispatches CPU indices sequentially. It is not evidence of AP startup or concurrent execution.
6. **ISO/installed-system acceptance remains pending:** a built ELF/ISO and a `KORONOS READY` marker are not a passing Live CD, installer, recovery, Aurora, or installed-disk boot.

## Validation added by this change

- Multiboot2 unit coverage for Live, installer, user-init ELF, and recovery module classification.
- Kernel build assertions for explicit handoff-blocker and recovery diagnostics.
- Kernel CI compiles/runs the Multiboot2 classification test.

## Required end-to-end acceptance

Run the normal project builder and boot tests after CI is green. Capture QEMU debugcon/serial output and require distinct target-specific markers:

- Live: module recognized, initramfs mounted/unpacked, `USERSPACE READY: init pid=...`, then Aurora/session readiness.
- Installer: installer process actually enters userspace, UI input/display becomes available, and disk-write stages are explicit and confirmed.
- Recovery: recovery init executes and exposes a working console.
- Installed OS: installation finishes on a disposable target disk, reboots from that disk, and reaches userspace-ready/Aurora markers.

Until these markers are produced by real execution, the corresponding target must remain blocked/not-ready. Do not test destructive installation against a user's real disk; use a disposable QEMU disk image first.
