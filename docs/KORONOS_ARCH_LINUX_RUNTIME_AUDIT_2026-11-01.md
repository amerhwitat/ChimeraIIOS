# Koronos vs Linux/Arch: kernel, boot and userspace audit (2026-11-01)

**Status: source audit and targeted ISO artwork fix in progress; production runtime remains blocked.** This document separates source presence, build evidence, kernel boot, candidate ring-3 probes, and production userspace acceptance. A successful ELF/ISO build is not a Linux-like userspace.

## 1. Comparison boundary

Arch Linux is a distribution built around the upstream Linux kernel. The kernel provides architecture bring-up, virtual memory, process/thread execution, syscalls, VFS, device and block/network interfaces, scheduling, security and drivers. Arch supplies the userspace integration and packages: an initramfs generator, systemd as PID 1, glibc and/or other runtime libraries, shell and core utilities, device management, package management (pacman), service units, logging and networking tools. Do not compare Koronos kernel code with Arch package names as if they were the same layer.

References:
- Arch boot and initramfs lifecycle: https://wiki.archlinux.org/title/Initramfs
- Arch installation/base userspace selection: https://wiki.archlinux.org/title/Installation_guide
- Arch system manager/PID 1: https://man.archlinux.org/man/init.1
- Linux process lifecycle: https://elixir.bootlin.com/linux/latest/source/kernel/fork.c and https://elixir.bootlin.com/linux/latest/source/kernel/exit.c
- Linux VFS: https://elixir.bootlin.com/linux/latest/source/fs/
- Linux syscall entry: https://elixir.bootlin.com/linux/latest/source/arch/x86/entry/
- Linux scheduler: https://elixir.bootlin.com/linux/latest/source/kernel/sched/

## 2. Current ChimeraIIOS main-branch findings

The main branch at audit time is `1694f610d5809b09e7247865be51ee0a335d18b1`. It contains the Koronos kernel, ELF admission and a generic ELF loader interface, but the production process path is not fully connected.

| Subsystem | Observed source/evidence | Comparison with Linux/Arch | Status |
|---|---|---|---|
| x86-64 kernel/boot | Freestanding Koronos ELF, Multiboot2 entry and kernel-ready smoke workflow exist | Equivalent only to kernel entry and early kernel initialization, not a full distribution boot | Build/boot evidence exists; target acceptance separate |
| ELF admission | `kernel/core/process.cpp` validates ELF64 headers, PT_LOAD ranges, entry permissions, W^X and allocates a kernel-owned PID record | Linux exec also creates a live mm/address space, stack/auxv and task context | Admission metadata exists; does not itself execute the process |
| ELF mapping | `kernel/core/process_loader.cpp` has callback-driven address-space creation, PT_LOAD mapping, BSS zeroing, stack mapping and rollback callbacks | Comparable loader primitives, but Linux connects these to the actual task/mm and scheduler | Reusable loader exists; production callback/target wiring is not proven on this main branch |
| User mode | No integrated `target_launch.cpp`, x86 user-entry assembly, or address-space backend is present in the current main-branch kernel tree | Linux has architecture-specific entry, task context and return-to-user paths | Main-branch integration gap |
| Syscalls | `kernel/core/syscall.cpp` is a compatibility translator; GETPID and EXIT/EXIT_GROUP fail closed without caller identity; only yield and timer ticks have simple handling | Linux syscalls operate on the calling task and implement defined errno, pointer and lifecycle semantics | Not a complete process-bound syscall ABI |
| VFS/fds | No demonstrated kernel-owned production root mount, per-process fd table, or full open/read/write/seek/close path | Linux VFS mediates path lookup, mount, permissions and file descriptors | Major blocker |
| Root/initramfs | ISO tooling stages Live and Recovery archives and manifests; staging is not the same as unpacking CPIO into a mounted kernel VFS | Arch early userspace runs /init as PID 1, discovers storage, mounts the real root and switch-roots | Production rootfs handoff not proven |
| Services | `kernel/core/service.cpp` validates dependency manifests and orders service IDs; bootstrap marks device/storage/security/logging/Kore as DECLARED | systemd starts services, tracks processes, restarts failures and reports health | Planner/state registry only; no proven service supervisor |
| Scheduler/SMP | `kernel/core/scheduler.cpp` runs callback tasks; `chimera_sched_run_parallel()` deliberately returns 0 because AP workers do not exist | Linux has task contexts, preemption, per-CPU runqueues, AP bring-up and SMP synchronization | Callback scheduler, not process scheduler or SMP |
| Devices/storage | A transport-neutral block interface and driver/catalog work exist; no production block backend + mounted persistent filesystem is proven | Linux block layer, drivers, udev and filesystems cooperate to mount root | Declared/partial |
| Userland/GUI | Rootfs command catalogs and Aurora/Marine assets/prototypes exist | Arch ships executable libc, dynamic loader, shell, coreutils, service manager, compositor/session and package manager | Catalog/artwork is not executable userspace acceptance |

### Important implementation distinction

The generic loader in `process_loader.cpp` is more than a metadata-only plan: it validates program headers, requests an address space through callbacks, maps pages with ELF permissions, zeros BSS and maps a user stack. However, the existence of this callback API does not establish that the current main-branch boot path supplies real callbacks, owns a saved user context, enters ring 3, or dispatches syscalls for that process. Keep those as separate gates.

The process table in `process.cpp` records admission and PID/state. It is not a task context, parent/child lifecycle, wait/reap implementation or context switch.

## 3. OctavianOS divergence that must be reconciled

OctavianOS currently vendors newer Koronos code under `vendor/chimera-ii-os/source/` that is not present in ChimeraIIOS main at the audit point. In particular, Octavian's vendored tree includes:
- `kernel/core/address_space.cpp`: x86-64 page-table/address-space backend, frame allocation, user mappings, NX/W^X checks, range validation and teardown.
- `kernel/core/target_launch.cpp`: selects one target-tagged USER_INIT_ELF module, admits and maps it, establishes an active PID/CR3, calls the architecture user-entry path, applies an in-kernel timeout and requires the init's readiness handshake.
- `kernel/arch/x86_64/user_entry.asm`: TSS/RSP0, ring-3 IRET entry, SYSCALL entry/return and timeout-abort continuation.
- `kernel/core/syscall.cpp`: a native single-process syscall dispatcher for GETPID, YIELD, TIME_TICKS, WRITE to console fds 0–2 (bounded to 4096 bytes), EXIT and EXIT_GROUP. Unsupported calls return ENOSYS. The separate compatibility dispatcher correctly rejects GETPID/EXIT when it has no caller context.
- `kernel/tests/user_init_smoke.c` and the six-case workflow: candidate probe ELFs and separate Live/Installer/Recovery × BIOS/UEFI QEMU checks.

This is meaningful progress beyond the current ChimeraIIOS main branch, but it remains a narrow single-init execution path. It does not provide general fork/clone, multiple runnable process contexts, a process-aware scheduler, file descriptors backed by VFS, open/read/close/seek, pipes, signals, dynamic linking, procfs/sysfs, service supervision, or AP/SMP scheduling. A candidate probe ELF is not the production initramfs or installed rootfs.

Do not silently assume vendored Octavian fixes are upstreamed to ChimeraIIOS. Port the code deliberately, preserve source provenance, and run the same tests in both repositories.

## 4. Current CI/runtime evidence

### ChimeraIIOS
- PR #215 branch `fix/squashfs-native-boot-contract-2026-10-29`, commit `d5435faef3876a768b3f5eaf2e6cec54de421ac7`, has a successful [Boot and ISO validation run #40774373176](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/40774373176). This is branch-specific build/boot evidence, not proof that current main has production userspace.
- Current main's most recent visible runs include Apache integration, vulnerability intelligence and Sentinel checks. Those do not test Koronos process execution or the six target/firmware cases.
- Current main still has no integrated target-launch/address-space/user-entry path as described above.

### OctavianOS
- The six-case [candidate ring-3 matrix #41325479648](https://github.com/amerhwitat/OctavianOS/actions/runs/41325479648) passed all Live/Installer/Recovery × BIOS/UEFI probe jobs. Each candidate trace showed a CPL3-originated syscall acknowledgement, readiness from the same nonzero PID, return to ring 3 and clean probe exit; BIOS cases also passed the in-kernel timeout/abort test.
- [Native Koronos run #41325460081](https://github.com/amerhwitat/OctavianOS/actions/runs/41325460081) passed its build job: x86-64 ELF/Multiboot2 validation, kernel-ready QEMU, Live/Recovery initramfs generation, ISO mastering, Octavian artwork rendering, strict final-ISO artwork extraction/byte comparison, target-routing smoke tests and full-ISO kernel-ready smoke. The overall workflow then **failed** in its separate production-userspace verifier.
- The production verifier reported all three Live/Installer/Recovery traces missing the CPL3-originated init syscall acknowledgement and actual init-PID readiness marker. Installer smoke logs state that production handoff is withheld because no supported native init ELF/runtime is wired; Recovery smoke logs state that no native recovery init ELF/runtime is wired. The full-ISO boot reaches kernel readiness and installer scaffolding, not a running installer GUI. Prerelease publication was skipped.
- The earlier #41245076234 failure was the Octavian artwork packaging defect; the strict artwork check now passes on #41325460081. The candidate ISO and Koronos ELF are retained as review artifacts, not releases.
- [Native kernel build workflow](https://github.com/amerhwitat/OctavianOS/actions/workflows/native-koronos-build.yml) and [six-case userspace acceptance workflow](https://github.com/amerhwitat/OctavianOS/actions/workflows/koronos-userspace-acceptance.yml) remain required for future changes.

## 5. Targeted ISO artwork fix included in the audit branch

The ISO builder now accepts optional, validated `CHIMERA_BOOT_ARTWORK_OVERRIDE` and `CHIMERA_BOOT_ARTWORK_MANIFEST` inputs. Default Chimera builds retain their existing artwork. Octavian's vendored ISO builder and native ISO workflow supply its rendered PNG and original-artwork manifest, so the same Octavian image is staged as the visual boot image and in Spit Fire/Jasper/GRUB/Koronos namespaces. The final-ISO verifier remains strict; the test is not weakened.

The ISO builders in both repositories now accept the same opt-in override contract; the Octavian workflow supplies its generated PNG and manifest. This change is carried in [PR #215](https://github.com/amerhwitat/ChimeraIIOS/pull/215). Chimera's updated [Boot and ISO validation run #41325458852](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/41325458852) passed with the default Chimera artwork path. The separate [Koronos boot matrix #41325458655](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/41325458655) was cancelled. The Octavian-specific override itself was verified by the strict ISO artwork extraction and byte-comparison step in [Octavian native build #41325460081](https://github.com/amerhwitat/OctavianOS/actions/runs/41325460081).

This validates the artwork packaging fix in Octavian; it does not change the kernel/userspace release gate.

## 6. Ordered Koronos implementation plan against Linux/Arch

1. **Finish rootfs/VFS:** bounded CPIO-newc parsing and extraction, real root mount, mount/node permissions, /dev, /proc, /sys, writable /tmp and persistent storage. Verify with actual open/read/close and write tests, including /etc/os-release.
2. **Finish process execution:** wire the real loader/address-space backend to a kernel-owned process object and saved architecture context; add user stack/auxv, faults, cleanup and process lifecycle.
3. **Finish native syscall ABI:** caller-owned PID, validated user buffers, fd table, open/read/write/seek/close, mmap/munmap, wait/exit, errno and negative-path tests. Keep compatibility translation separate from native syscall dispatch.
4. **Build a real PID 1/service manager:** mount early filesystems, start service executables, dependency failure propagation, health checks, restart/reap, logs and target completion.
5. **Implement core userland:** native libc/sysroot, dynamic loader (or explicitly static-only scope), shell, core utilities, package database/installer, device management, networking tools and runtime metadata.
6. **Add Linux-compatible interfaces selectively:** procfs/sysfs, signals, pipes/IPC, sockets, poll/event interfaces and ioctl/device ABI. Document unsupported calls; do not advertise full Linux compatibility from a syscall-number map.
7. **Finish SMP and drivers:** AP startup, per-CPU state, interrupt/timer handling, process context switching, block/network/input/display/audio drivers and real device tests.
8. **Qualify all targets:** six independent Live/Installer/Recovery × BIOS/UEFI boots from one ISO SHA; same nonzero PID for CPL3 syscall acknowledgement and userspace-ready; Aurora health; installer write + cold reboot persistence; recovery postcondition; overlapping execution on at least two CPUs.

## 7. Release gate

Keep release publication fail-closed. A kernel-ready marker, a candidate ring-3 smoke ELF, an ISO artifact, a static contract test, or a successful artwork check cannot substitute for production init execution. Link every acceptance trace and artifact to the exact commit and ISO SHA. Do not claim Arch/Linux userspace parity until the supported ABI and runtime components pass real user-mode tests.
