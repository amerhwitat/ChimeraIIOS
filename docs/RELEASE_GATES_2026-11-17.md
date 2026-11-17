# Koronos native execution and ISO release gates — 2026-11-17

This document is an evidence ledger and implementation order. It does not mark any target production-ready merely because an ELF compiles or a CI metadata check passes.

## Verified source state

The current `main` source inspected on 2026-11-17 contains:

- `kernel/core/target_launch.cpp`: selects exactly one `USER_INIT_ELF`, admits and maps it, installs its CR3, enters ring 3, requires a CPL-3-origin syscall acknowledgement and target/PID readiness marker, and enforces a PIT deadline. It then destroys the address space and returns to the kernel.
- `kernel/core/process.cpp` and `kernel/include/chimera/process.h`: a bounded process admission/state table. The public header still defines `CHIMERA_PROCESS_LOAD_PLAN_ONLY`; this table is not a persistent process scheduler.
- `kernel/core/scheduler.cpp`: callback-task scheduler. Tasks are function callbacks, not saved user CPU contexts. `chimera_sched_run_parallel()` intentionally returns zero because AP startup/per-CPU workers are not implemented.
- `kernel/targets/live_init.c`, `installer_init.c`, and `recovery_init.c`: ring-3 readiness probes, not full target operating environments.
- The Multiboot2 initramfs modules remain payload data; the freestanding path does not yet unpack and mount a usable root filesystem with `/dev`, `/proc`, `/sys`, writable `/tmp`, and VFS-backed open/read/write/exec.
- The installer lacks a production block-device writer and persistence verification. Recovery is diagnostics-only without filesystem/boot repair execution. Aurora/Marine do not yet have a verified freestanding compositor/session.

## Linux reference contract

Use the Linux boot/init sequence as a behavioral reference, not as code to copy wholesale:

1. Discover and validate boot modules.
2. Unpack initramfs and establish the initial root namespace.
3. Create PID 1 as a real process with a kernel-owned address space, mapped ELF segments, user stack, saved architecture context and kernel stack.
4. Make PID 1 runnable and start the process-aware scheduler.
5. Keep PID 1 alive; it launches and supervises target services and reaps children.
6. Report readiness only after PID 1 has mounted required pseudo-filesystems, started required services and completed its target handshake.

Reference: Linux `init/main.c`, especially `rest_init()`, `kernel_init()`, `kernel_init_freeable()`, and the init executable selection path.

## Required kernel implementation sequence

### Gate K1 — persistent process contexts and PID 1

- Replace callback-only scheduling for user processes with a process object owning PID/PPID, lifecycle state, CR3/address-space ownership, kernel stack, user stack, saved interrupt/syscall context, scheduling class/priority, CPU affinity and wait/exit status.
- Reserve PID 1 during bootstrap; never recycle it while the init process is alive.
- Add architecture context save/restore on timer preemption and voluntary yield. Keep interrupt entry, syscall entry and scheduler switch paths on a known-good kernel stack/TSS RSP0.
- Add `fork/exec`-equivalent process creation or a documented minimal spawn contract, `exit`, `wait/reap`, blocking/wakeup and signal/termination semantics.
- Add reference-counted address-space cleanup and rollback on partial ELF load failures.
- Keep callback tasks as kernel work items; do not count them as processes.
- Tests must cover PID 1 persistence, two runnable user contexts, timer preemption, yield, block/wakeup, exit/reap, malformed ELF, address-space isolation and PID accounting.

### Gate K2 — initramfs and VFS

- Validate module bounds, compression and cpio entries before extraction; reject path traversal, duplicate unsafe paths and malformed archives.
- Mount a read-only base root and writable tmpfs overlay or equivalent.
- Implement the minimum VFS contract and mount points `/dev`, `/proc`, `/sys`, `/tmp`, `/run`.
- Provide console/tty and device discovery before launching PID 1.
- Implement open/read/write/close/stat/readdir/exec/wait semantics required by the init and service manager.
- Add tests that execute files from the mounted rootfs, not directly from Multiboot module memory.

### Gate K3 — three target init systems

- Live: persistent PID 1, service manager, shell/login or session, networking/storage discovery, and explicit shutdown/reboot.
- Installer: same rootfs/process contract plus block-device inventory, explicit destructive-operation confirmation, partition table writer, filesystem creation, file copy, bootloader install, fsync/read-back verification and reboot test in disposable virtual disks.
- Recovery: read-only discovery first, explicit repair plan, journal/filesystem repair adapters, boot-entry repair, before/after reports and post-repair verification.
- Each target must have its own manifest, init ELF, rootfs, service definitions and target-specific integration tests.

## Desktop, application and media gates

- Build and package Aurora Glass, Marine Blue, FreeXP and FreeWin11 as selectable desktop sessions; keep Aurora as default unless a valid user preference selects another.
- A preview shell is not a production desktop. Require a real display server/compositor, input, window management, graphics backend, session manager, file manager, terminal, settings and logout/shutdown path.
- Stage icons, fonts, wallpapers, images and video with license/provenance manifests and checksums. Include each artifact only when a real application/session references it; test the ISO media paths and launch behavior.
- OpenGL/OpenCV packages must be linked to tested ABI/runtime providers. Package presence alone is not an integration test.
- DOSBox-X, Amiga and Commodore emulators require executable provider builds and legal, redistributable media. Do not bundle copyrighted ROMs/disks without redistribution rights.

## Commands, ISA and compatibility gates

- Generate a command-provider ledger keyed by namespace + normalized command ID. Each row must record upstream source, license, package/binary hash, target architecture, install result, smoke test and runtime conformance. Unavailable entries stay unavailable.
- Keep Linux/Bash, macOS, Windows CMD, PowerShell, SQL Server and Native Chimera namespaces distinct. A name crosswalk is not semantic equivalence.
- For every ISA architecture, record exact revision/extensions/ABI, toolchain triple, assembler/compiler, linker/sysroot, binary header, decode/encode vectors, semantic tests, differential tests and runtime result.
- Do not call a compile-only object an executable OS binary or an architecture conformance pass.
- Use Wine/Darling/QEMU user-mode only within their supported compatibility boundaries; do not imply that they replace a Windows/macOS kernel.

## Mobile and flashing gates

- The current mobile image builder explicitly produces a research layout and stops before device signing/flashing.
- A flashable release requires an exact device codename, kernel, DTB/DTBO, vendor modules, partition map, AVB/signing chain, rollback policy, recovery path, image hashes and a tested vendor transport adapter.
- Keep generic partition writes and bootloader/authentication bypasses disabled. Run device discovery and image verification before any write; require explicit confirmation and a tested recovery procedure.

## Immutable ISO acceptance matrix

Build once, calculate SHA-256, and run the exact same ISO bytes through all six cases:

| Target | BIOS | UEFI |
|---|---|---|
| Live | Required | Required |
| Installer | Required | Required |
| Recovery | Required | Required |

For each case archive the QEMU command line, firmware version, serial trace, screenshot if applicable, disk fixture hashes, exit code and ISO SHA-256. The verifier must prove the ordered kernel-ready → CPL-3 init syscall acknowledgement → same nonzero PID userspace-ready sequence. Installer must prove writes and reboot persistence on a disposable disk. Recovery must prove a real repair and post-repair verification. Live must prove persistent PID 1 and a usable session.

## Current release decision

**BLOCKED — no production ISO release is authorized by the source evidence inspected on 2026-11-17.**

The existing handoff probes and structural CI are useful intermediate checks. They do not satisfy K1–K3, target behavior, desktop runtime, mobile signing, complete command/ISA conformance, or the six-case immutable-ISO matrix. Do not publish an ISO or label a phone image flashable until those gates have passing, reproducible evidence.
