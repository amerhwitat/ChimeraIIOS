# Cross-platform implementation references and native acceptance policy

This document defines how Linux, Windows and macOS are used as engineering references for ChimeraIIOS/Koronos. It does not claim binary, ABI or source compatibility with those operating systems.

## Reference mapping

| Area | Linux reference | Windows reference | macOS reference | Koronos requirement |
|---|---|---|---|---|
| Firmware and boot | UEFI/GRUB, initramfs and kernel handoff | UEFI + Windows Boot Manager/BCD | EFI boot policy and boot.efi | Spit Fire/Jasper/GRUB may load the same immutable Koronos ISO in BIOS and UEFI; firmware identity comes from the actual GRUB platform token |
| First userspace | initramfs root and PID 1 | Session Manager / native subsystem startup | launchd bootstrap | A real target-specific ring-3 init ELF, kernel-owned nonzero PID, syscall acknowledgement and userspace-authored readiness |
| Service graph | systemd units, targets and dependency ordering | Service Control Manager dependencies and recovery actions | launchd jobs and service domains | Explicit Live, Installer, Recovery and desktop service dependencies; no menu label may imply a service is running |
| Filesystem | VFS, mount namespaces, tmpfs, procfs and sysfs | NT object/file APIs and NTFS volume semantics | VFS/APFS and volume snapshots | Real kernel VFS and block/filesystem drivers; root mount plus write/read of /tmp; descriptor and error semantics tested from CPL3 |
| Process/scheduling | exec, wait, signals, preemption and per-CPU run queues | process/thread objects, APC/IRQL and scheduler diagnostics | Mach tasks/threads and scheduler | Owned address spaces/stacks, exit/wait/reap, AP startup, per-CPU state and independently overlapping tasks |
| Installation/recovery | partitioning, filesystem checks, initramfs recovery | Windows Setup/WinRE and rollback | installer plus APFS snapshots/recovery | Durable write followed by cold-boot verification; repair transaction followed by independently checked postcondition |
| Desktop/input | Wayland/X11 compositor and seat/input stack | Win32 message/input model and DWM | WindowServer, AppKit and LaunchServices | Actual Aurora and Marine processes, compositor/input health, app launch and clean shutdown—not static assets or screenshots |

## CI host responsibilities

- **Linux runners** are the canonical environment for native freestanding kernel builds, ISO mastering, QEMU BIOS/UEFI boots, initramfs inspection, filesystem tools and reproducible SHA-256 evidence.
- **Windows runners** validate Windows SDK/toolchain compatibility (MSVC/clang-cl where available), PE/COFF packaging, Win32 input/event contracts and application build/install/uninstall behavior. They do not replace QEMU boot evidence for Koronos.
- **macOS runners** validate Apple Clang/Xcode, Objective-C/Foundation and Darwin SDK compatibility, signing/packaging metadata and desktop integration. Apple SDKs and proprietary system components must not be copied into the ISO.
- A green host build is only a host-build result. It does not establish that the native kernel, firmware boot, userspace, filesystem, installer or desktop works.
The repository host checks are defined by .github/workflows/chimera-build-matrix.yml (Linux/Windows/macOS portable CMake builds) and .github/workflows/apple-build.yml (Apple toolchain/project validation).

## Same-ISO six-case runner

The runner at tools/boot/run-six-case-qemu.py boots the already-built canonical ISO for Live, Installer and Recovery under BIOS and UEFI. It does not remaster or rewrite the ISO between cases. The manifest binds every attempted case to the SHA-256 computed from that ISO, and raw QEMU debugcon/serial traces are retained.

GRUB supplies firmware=$grub_platform on the selected target-init module command line. Koronos logs BOOT FIRMWARE: BIOS for pc and BOOT FIRMWARE: UEFI for efi. The runner itself never inserts readiness, VFS, SMP, desktop, persistence or recovery markers into the trace.

The runner is a diagnostic evidence collector, not an acceptance shortcut. Its output must pass tools/boot/verify-six-case-matrix.py. Missing traces, incorrect menu selection, missing firmware identity, missing desktop/postcondition traces, native-init exit 78, VFS gaps or absent real SMP evidence remain BLOCKED.

## Known native gaps that must be implemented, not simulated

- The current native Live init is a ring-3 console payload; it does not start Aurora or Marine.
- The current Installer init is explicitly a storage-plan dry run; it does not write a block device.
- The current Recovery init is diagnostic; it does not perform a repair transaction.
- The kernel's production VFS/syscall path does not yet demonstrate a mounted native root and writable /tmp from ring 3.
- Scheduler callback stepping is serial. chimera_sched_run_parallel() remains fail-closed until AP startup, per-CPU workers, synchronization and measured concurrent work are real.
- BIOS and UEFI QEMU traces are necessary but not sufficient. Installer persistence requires a second cold boot of the installed disk; Recovery requires a real repair and verified postcondition.

## Release policy

Native Koronos release requires exactly six target/firmware records, all bound to the same immutable ISO SHA-256, with ordered kernel-ready → CPL3 syscall acknowledgement → matching nonzero PID readiness. It also requires runtime firmware identity, native root and /tmp operations, two online CPUs with measured overlap, Aurora and Marine session traces, installer cold-boot persistence and Recovery repair postcondition.

Native-init exit 78 remains a hard failure. Synthetic fixtures test only the verifier. Kernel-only smoke boots, target-specific remastered probe ISOs, Linux live editions, host SDK builds and documentation do not satisfy production acceptance.
