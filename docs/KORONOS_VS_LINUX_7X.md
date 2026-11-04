# Koronos vs. Linux 7.x — subsystem comparison and reference workflow

Status: 2026-11-04. Linux is an engineering reference, not copied code or a claim of Linux ABI compatibility. This document describes the current source boundary; only exact-head CI and genuine runtime evidence can promote a capability to accepted.

## 1. Workflow comparison

| Linux workflow | Koronos counterpart | Current boundary |
|---|---|---|
| Firmware and architecture setup: EFI stub/boot protocol, early CPU state, memory map | Jasper/GRUB Multiboot2 handoff, BSP setup, physmap and frame allocator | GRUB owns BIOS/UEFI firmware transition. BSP is initialized; APs are not online. |
| initramfs unpacked into rootfs; PID 1 starts | CPIO-newc payload modules and target-specific ring-3 ELF | Init ELF is launched; production CPIO extraction/rootfs handoff is not yet wired. VFS currently supplies a bounded kernel root and tmpfs. |
| `task_struct`, `mm_struct`, `copy_process`, exec/wait/reap | process admission records, per-process CR3 loader and PID-keyed FD table | Process records still describe an ELF load plan. No scheduler-owned saved trap-frame task lifecycle, parent/child wait, or real exec yet. |
| `copy_from_user` / `copy_to_user` with fault-aware access | current-CR3 page-table range validation and bounded copy helpers | Covered pages are checked before copy, but pages are not pinned and kernel page-fault fixup/recovery is not yet guaranteed. |
| VFS `open/read/write/lseek/close`, file objects and per-task descriptors | bounded root VFS, tmpfs, PID-keyed descriptor table, CPL3 syscall dispatch | OPEN/READ/WRITE/SEEK/CLOSE are routed for the active native init process. The VFS is initialized at target launch; runtime round-trip tests are present in the explicit test ELF. Production acceptance still requires exact-head successful QEMU traces. |
| systemd/PID 1 service supervision and dependency graph | Kore service orchestration and target init | One target init is launched and reaped synchronously. General child supervision and service lifecycle are incomplete. |
| x86 topology discovery + ACPI MADT + AP INIT/SIPI + per-CPU runqueues/IPIs | CPUID topology, MADT entry parser, APIC and scheduler foundations | CPUID topology is implemented. MADT entry parsing is implemented and host-tested in CI; ACPI table discovery/runtime parser wiring, AP INIT/SIPI, per-CPU interrupt state/IPIs and online acknowledgements remain outstanding. Scheduler remains BSP-only. |
| `blk-mq`, partition/filesystem drivers, installer writes | Koronos block layer and Installer transaction | Installer remains a storage-plan dry run. No durable disk writes or cold-boot persistence are claimed. |
| fsck/repair and verified root postconditions | Koronos Recovery transaction | Recovery remains diagnostics-only; no repair postcondition is claimed. |
| Wayland compositor and user sessions | Aurora Wayland Glass / Marine session processes | Native target init is a text console. Actual Aurora and Marine guest sessions are not yet proven by native Koronos traces. |

## 2. Linux-inspired implementation sequence

1. **Build/boot:** Kbuild/Kconfig-style object graph, architecture entry, firmware handoff and physical memory map.
2. **Early userspace:** validate and unpack CPIO-newc; construct rootfs; mount /dev, /proc, /sys and writable /tmp; launch PID 1.
3. **Process/syscall boundary:** task-owned address spaces, guarded kernel stacks and saved trap frames; validated user copies; per-process descriptor tables; syscall VFS routing.
4. **Lifecycle/supervision:** scheduler-owned context switches, process exit, wait, reap and descriptor/address-space cleanup; service dependency supervision.
5. **SMP:** CPUID + ACPI topology discovery; BSP/AP per-CPU setup; INIT/SIPI and AP acknowledgements; IPIs/TLB shootdown; per-CPU runqueues; concurrent work measurement.
6. **Targets:** real Live session, transactional Installer with cold reboot, Recovery repair with independently checked postcondition.
7. **Acceptance:** six Live/Installer/Recovery × BIOS/UEFI boots of one immutable ISO SHA-256 with the same genuine target-specific CPL3/PID/VFS chain and all target-specific postconditions.

## 3. CPU discovery versus CPU availability

| Evidence | What it proves | What it does not prove |
|---|---|---|
| CPUID leaf 0x1F/0x0B or AMD 0x8000001E | Package logical count, core/SMT topology and BSP APIC identity | APs are initialized, online or schedulable |
| ACPI MADT type 0/type 9 parser | Bounded decoding of Local APIC/x2APIC processor entries, duplicate/bounds checks, BSP membership | ACPI root-table discovery, AP startup or online acknowledgements |
| Scheduler CPU count = 1 | Only BSP is scheduler-online | SMP capability |
| Serial callback stepping / affinity metadata | Deterministic scheduler tests and policy metadata | Simultaneous execution |
| Overlapping monotonic intervals tagged with distinct online APIC IDs | Measured concurrent work on at least two CPUs | Installer/recovery or six-case acceptance |

The new `kernel/core/apic_topology.cpp` parser is compiled into Koronos and exercised by `tests/kernel/run-apic-topology-host-tests.sh`. Its output must not be used to increase the scheduler's online CPU count before actual AP startup and acknowledgement.

## 4. Build workflow and parallelism

Koronos follows the useful Kbuild model: per-directory source ownership, generated object rules, explicit configuration, dependency-aware parallel compilation, separate host tests, and a legacy build entry point. The builder's host-test stage is sequential today; object compilation can be parallelized only after dependency generation and deterministic output paths are correct.

Linux `make -jN` is safe because Kbuild tracks generated dependencies and target ownership. Koronos should not equate `-j` with runtime SMP. Build parallelism and kernel runtime parallelism are separate acceptance dimensions:
- build jobs may run concurrently on host cores;
- runtime APs need real startup, per-CPU stacks/GDT/TSS/GS, scheduler contexts, locking, IPIs and measured overlap;
- CPU topology discovered by CPUID/MADT is inventory, not online state.

## 5. Evidence and release boundary

The required chain remains:

`kernel-ready` → genuine CPL3 syscall acknowledgement → `NATIVE INIT PID: target=... pid=...` → userspace-authored `USERSPACE READY: target=... init_pid=...`.

All six target/firmware traces must refer to the same immutable ISO SHA-256. They must also prove root `/etc/os-release` OPEN/READ/CLOSE, writable `/tmp`, target-specific health, installer persistence after a separate cold boot, Recovery repair postcondition, and measured overlap on at least two CPUs.

The explicit test ELF's VFS exercise is a test probe, not production readiness evidence. Kernel-only QEMU smoke, host tests, topology counts, serial stepping, Linux live editions, screenshots, build success and documentation do not substitute for these gates.

Native-init exit 78 remains a hard failure. Do not promote test ELFs, synthesize readiness, weaken the verifier, merge the draft PRs, or publish a release until all required evidence passes.
