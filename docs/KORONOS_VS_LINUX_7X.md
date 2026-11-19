# Koronos vs. Linux 7.x — subsystem comparison and reference alignment

Status: living document, 2026-11-04. Scope: the Koronos microkernel shipped in
`kernel/` (Chimera II OS) and `vendor/chimera-ii-os/source/kernel/` (OctavianOS),
the ring-3 target payloads in `kernel/targets/`, and the ISO/userspace build.

This document exists because the project is deliberately built *with Linux as the
reference model* — the same boot contract, the same build ergonomics, the same
"init is a userspace program" boundary — without claiming Linux compatibility.

## 1. Subsystem map

| Concern | Linux 7.x reference | Koronos today | Gap / decision |
| --- | --- | --- | --- |
| Boot protocol | 32/64-bit boot protocol, EFI stub, `boot_params` | Multiboot2 via GRUB 2.12 (`multiboot2 /boot/koronos/koronos.elf`) | No EFI stub: firmware support is delegated to GRUB, not to Koronos. Keeping GRUB keeps BIOS+UEFI parity in one image. |
| Early memory map | E820 / EFI memory map → memblock | Multiboot2 memory map → `physmap`, `frame_allocator` | **Aligned in shape**: a physical allocator over a described map, 4 KiB frames, above-4-GiB ranges rejected at bootstrap (documented contract, host-tested). |
| Kernel address space | `swapper_pg_dir`, direct map, KASLR | `koronos_bootstrap_pml4`, higher-half kernel, per-process PML4 (`address_space`) | No KASLR, no direct map aliasing beyond the physmap contract. |
| Process model | `task_struct`, `mm_struct`, `copy_process` | `process.cpp` records + `address_space.cpp` (per-process CR3) | No fork/exec: exactly one admitted init per boot. Deliberate: the acceptance contract asks for one real init. |
| User entry | `iretq` to `start_thread`, TSS `RSP0` | `user_entry.asm`: GDT user descriptors, 64-bit TSS, `ltr`, `RSP0`, `iretq` trampoline | **Implemented and evidenced** (see §3). |
| Syscall entry | `MSR_LSTAR`/`syscall`, `swapgs` | `syscall` with STAR/LSTAR set up in `user_entry.asm`; `syscall.cpp` dispatcher; `INT 0x80` DPL3 gate for the CPL-3 proof | Linux uses `syscall` as the fast path and `int3`/`int 0x80` only for compat. Koronos keeps `INT 0x80` as the *audit* gate so the kernel can prove `CS.RPL == 3` before it acknowledges anything. |
| PID namespace | `struct pid`, `task_pid_nr` | kernel-owned per-process id, returned by `CHM_SYS_GETPID` | Payloads never embed PID 1; the verifier requires the PID the kernel assigned. |
| Signals / waits | `signal_struct`, wait queues | APC/DPC queues, `chimera_wait_one` | Not POSIX. |
| Scheduler | CFS/EEVDF, per-CPU runqueues and preemptive task contexts | callback task queue (`chimera_sched_run_once`); `chimera_sched_run_parallel` returns zero | **Not process scheduling.** There is no saved user register context, timer-driven process preemption, AP startup, or per-CPU runqueue dispatch. |
| Block layer | `bio`, request queues, `blk-mq` | none exposed to ring 3 | **Installer payload must stay a dry-run report** until a block backend exists. Do not advertise installation. |
| VFS | `struct super_block`, `dentry` | none (filesystem code exists in `filesystems/` for research, not wired to syscalls) | No `open/read/write` on files; `write` targets fd 1 only. |
| Console | `tty`, `printk` → serial/VT | `console_write` → debugcon/serial, `pc-display` driver | Userspace writes go through `CHM_SYS_WRITE` to the same console. |
| Build system | Kbuild/Kconfig, `make defconfig`, `-j`, modules | `kernel/Kbuild` + `Kconfig` + `scripts/kconfig`, `make -C kernel defconfig && make -C kernel -j`, `make modules`, `make install` | **Aligned**: Linux-style targets and per-directory `Kbuild` fragments; the legacy `build-koronos.sh` recipe is retained as `make legacy`. |
| Module model | `insmod`, ELF relocations, vermagic | Multiboot2 modules (`module2`), typed by name (`chimera-live-initramfs`, `chimera-installer-contract`, `chimera-user-init-elf`, …) | Modules are staged by the ISO, not loaded at runtime. |
| Init contract | `/sbin/init`, persistent PID 1, `execve` | one target-specific `chimera-user-init-elf` probe per boot | **Probe only.** Current target launcher enters ring 3 synchronously, waits for return, destroys the address space, and marks the process exited. It is not a persistent PID 1 or service manager. |
| Initramfs | cpio + gzip/zstd, unpacked by the kernel | cpio+gzip image staged as a Multiboot2 module, surfaced to the target | The initramfs is *payload data* today, not an unpacked rootfs. |
| Verification | boot selftests, `kselftest`, CI | fail-closed trace verifier (`tests/*/verify-userspace-handoff.py`), QEMU BIOS+UEFI matrix | Kept intentionally stricter than the kernel it validates: marker must come from user code after a CPL-3 syscall. |

## 2. What "use Linux as the reference" changed in this tree

1. **Kbuild/Kconfig front end** (`scripts/kconfig/kconfig.py`, `scripts/kbuild/obj2mk.py`,
   per-directory `Kbuild`): `make -C kernel defconfig`, `make -C kernel -jN`,
   `make -C kernel modules|modules_install|install|check`, `make legacy` for the old
   monolithic recipe. The `MAKEFLAGS += --no-print-directory`, `.PRECIOUS` config
   handling and `.NOTPARALLEL` config rule are direct answers to Kbuild's
   "regenerated makefile is intermediate" behaviour.
2. **Userspace boundary**: init is a normal ELF (`ET_EXEC`, one `LOAD` segment with
   `R E`, entry at `0x1_0000_0000`) built freestanding with the same flags Linux uses
   for early userspace (`-ffreestanding -fno-stack-protector -mcmodel=large -mno-red-zone`).
3. **Target selection** mirrors Linux's "one init, selected by the bootloader":
   GRUB passes exactly one `chimera-user-init-elf` module and its `target=` cmdline.
   Installer and Recovery are *not* fallbacks for Live; ambiguous selection is rejected.
4. **`/proc`-style introspection**: `chm.log=`/`chm.progress=` cmdline switches and the
   `[KRN ]/[RUN ]/[SCH ]/[MM  ]` tag prefixes give the same "read the boot log" workflow
   `dmesg` gives on Linux.

## 3. Evidence status — source audit, not production acceptance

The current source contains a real x86-64 ring-3 entry path and a target/PID-specific
readiness-probe contract. That is useful progress, but it must not be conflated with
a production userspace runtime.

| Capability | Current source status |
| --- | --- |
| ELF validation and PT_LOAD mapping callbacks | Implemented; hardware permission enforcement and full lifecycle still require independent verification |
| CR3 activation and ring-3 entry | Synchronous x86-64 entry path exists |
| CPL3-originated syscall acknowledgement | Implemented in the probe path; must be confirmed in fresh QEMU traces |
| Target/PID readiness marker | Probe contract exists; a marker is not proof of a persistent init |
| Persistent PID 1 and process-aware scheduler | NOT IMPLEMENTED |
| Initramfs unpacking and mounted rootfs/VFS | NOT IMPLEMENTED |
| Live shell and native desktop startup | NOT IMPLEMENTED on the freestanding Koronos path |
| Installer disk writes and reboot persistence | NOT IMPLEMENTED |
| Recovery repair operations and postcondition checks | NOT IMPLEMENTED |
| AP startup and real parallel SMP | NOT IMPLEMENTED |

Do not reuse historical six-case PASS statements as current release evidence. A valid
release claim requires fresh traces from the exact immutable ISO SHA, with the
unchanged fail-closed verifier, plus separate Live desktop, installer persistence,
Recovery repair, and AP-concurrency acceptance tests. The current readiness ELF
manifests explicitly identify their payloads as probes and set
`production_ready=false`.

## 4. Deliberate non-goals

- No Linux ABI compatibility: no `open/read/mmap/fork/execve`, no VFS, no `io_uring`.
- No claim of production readiness for the native desktop: Aurora is an HTML/JS
  desktop that runs in the Linux live session; the native targets are text-mode
  userspace payloads.
- No installer disk writes: without a block backend the installer target reports a
  plan and exits. The installer text says so explicitly.

## 5. Next alignment steps (ordered)

1. Block-device syscall surface (read/write sectors on the boot medium) so the
   installer target can move from dry-run to a real, verified partition write.
2. Initramfs unpacking in-kernel (cpio reader → tmpfs-like ramfs) so Live can own a
   real root instead of relying on payload modules.
3. Per-CPU AP bring-up with per-CPU evidence, then scheduler claims.
4. `MSR_LSTAR`-only syscall path with `swapgs`, keeping `INT 0x80` as the audit gate.
