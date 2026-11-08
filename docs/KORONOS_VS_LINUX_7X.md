# Koronos vs. Linux 7.x — subsystem comparison and reference alignment

Status: living document, updated 2026-11-08. Scope: the Koronos microkernel shipped in
`kernel/` (Chimera II OS) and `vendor/chimera-ii-os/source/kernel/` (OctavianOS),
the ring-3 target payloads in `kernel/targets/`, and the ISO/userspace build.

## Current upstream reference baseline

- Linux stable: **7.3.3** (2026-11-06); mainline: **7.4-rc1** (2026-11-01); LTS: **6.18.62** (2026-11-06). Source of truth: [kernel.org release index](https://www.kernel.org/).
- Early userspace reference: [Linux initramfs documentation](https://docs.kernel.org/filesystems/ramfs-rootfs-initramfs.html). Linux extracts the initramfs archive into rootfs and invokes `/init`; merely loading a Multiboot2 module is not equivalent.
- Target/service reference: [systemd boot-up and target ordering](https://github.com/systemd/systemd/blob/main/man/bootup.xml). Dependencies are activated in parallel where possible, while `sysinit`, `basic`, `multi-user`, and `graphical` provide explicit ordering boundaries.

These are architectural references, not claims that Koronos implements Linux's full boot ABI or systemd compatibility.

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
| Scheduler | CFS/EEVDF, per-CPU runqueues | priority queues, `chimera_sched_run_parallel`, per-CPU snapshots | SMP is scheduled but AP bring-up is not proven; `-smp 2` alone is not evidence. |
| Service/target manager | systemd unit dependency graph; parallel activation with ordered `sysinit`, `basic`, `multi-user`, `graphical` targets | Kore now has a dependency resolver, explicit service states, start/health callbacks and host contract tests | The callbacks are not yet wired to real storage/VFS/network/display providers; core services remain DECLARED. Add a target graph and require provider health before any mode target can be reached. |
| Block layer | `bio`, request queues, `blk-mq` | none exposed to ring 3 | **Installer payload must stay a dry-run report** until a block backend exists. Do not advertise installation. |
| VFS | `struct super_block`, `dentry`, file descriptors and filesystem operation vectors | no production VFS; filesystem code in `filesystems/` is not wired to syscalls | No general `open/read/write/close/seek` on files; console-only read/write remains. No `/etc/os-release` file-open proof or writable `/tmp`. |
| Console | `tty`, `printk` → serial/VT | `console_write` → debugcon/serial, `pc-display` driver | Userspace writes go through `CHM_SYS_WRITE` to the same console. |
| Build system | Kbuild/Kconfig, `make defconfig`, `-j`, modules | `kernel/Kbuild` + `Kconfig` + `scripts/kconfig`, `make -C kernel defconfig && make -C kernel -j`, `make modules`, `make install` | **Aligned**: Linux-style targets and per-directory `Kbuild` fragments; the legacy `build-koronos.sh` recipe is retained as `make legacy`. |
| Module model | `insmod`, ELF relocations, vermagic | Multiboot2 modules (`module2`), typed by name (`chimera-live-initramfs`, `chimera-installer-contract`, `chimera-user-init-elf`, …) | Modules are staged by the ISO, not loaded at runtime. |
| Init contract | `/sbin/init`, PID 1, `execve` | one selected ring-3 target-console ELF per boot with `target=live|installer|recovery` | Console handoff is smoke-tested, but the payload explicitly reports that VFS, external ELF execution and graphics are not enabled. Its readiness marker is not full OS/desktop readiness. |
| Initramfs | CPIO archive extracted into rootfs; kernel then executes `/init` as PID 1 | Existing media still stages gzip-compressed CPIO as a Multiboot2 payload. A bounded freestanding CPIO-newc scanner has been added for uncompressed archives, with path/duplicate/truncation/CRC checks and all-or-nothing callbacks; it is not yet wired to a boot module or mount path | Add an uncompressed native archive module, connect the scanner to the kernel boot path, then publish entries through a real VFS. Gzip decompression and VFS publication remain absent. |
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

## 3. Evidence produced by this build

The release archive records six BIOS/UEFI target-console handoff smoke cases. These prove that the selected ring-3 console payload can enter, issue its audited syscall, and emit a same-PID console marker. They do **not** prove a mounted root filesystem, general file syscalls, a production installer, recovery repair, a graphical session, or SMP.

| Case | Recorded evidence scope |
| --- | --- |
| Live / BIOS + UEFI | Target-console ring-3 handoff smoke only |
| Installer / BIOS + UEFI | Safe installer console; disk writes remain disabled |
| Recovery / BIOS + UEFI | Diagnostic console; filesystem repair remains unavailable |

The production release gate additionally requires `/etc/os-release` OPEN/READ/CLOSE,
writable `/tmp`, installer cold-boot persistence, recovery repair postconditions,
native desktop health on Live BIOS+UEFI, and measured overlap on at least two CPUs.
A console marker alone cannot satisfy these gates.

Verifier sources: `tests/migration/verify-userspace-handoff.py` (OctavianOS) and
`tests/boot/verify-userspace-handoff.py` (Chimera II OS).

## 4. Deliberate non-goals

- No Linux ABI compatibility: no `open/read/mmap/fork/execve`, no VFS, no `io_uring`.
- No claim of production readiness for the native desktop: Aurora is an HTML/JS
  desktop that runs in the Linux live session; the native targets are text-mode
  userspace payloads.
- No installer disk writes: without a block backend the installer target reports a
  plan and exits. The installer text says so explicitly.

## 5. Next alignment steps (ordered)

1. Stage an uncompressed native CPIO-newc module for each target and wire the
   bounded scanner into Multiboot2 module validation.
2. Publish a read-only initramfs root through a real VFS; add tmpfs for writable
   `/tmp`, then test path traversal, permissions, corruption and teardown.
3. Implement process-owned file descriptors and validated `OPEN/READ/WRITE/CLOSE/SEEK`
   routes. Require the `/etc/os-release` and `/tmp` probes from actual ring-3 init.
4. Wire real service start/health callbacks and a dependency graph for
   `sysinit`, `basic`, `multi-user`, `graphical`, `live`, `installer`, and `recovery`.
5. Implement block-device drivers, partition discovery, a native filesystem and
   verified installer persistence; then recovery check/repair/rollback semantics.
6. Bring up APs and implement process-aware preemptive scheduling, per-CPU runqueues,
   TLB shootdowns and measured two-CPU overlap.
7. Implement a native display server (X11 or a defined native compositor/display
   protocol), GPU/input paths and desktop-session health checks. Browser WebGL in
   the Linux-hosted edition is not a native Koronos graphics stack.
8. Add other Koronos architectures only after each has a real bootloader handoff,
   kernel, HAL, drivers, userspace ABI and hardware/QEMU acceptance matrix.
