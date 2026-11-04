# Chimera II OS — native Koronos ISO chimera-ii-native-2026.11.04

Single hybrid BIOS+UEFI image whose GRUB menu boots the Koronos microkernel and hands
Live, Installer and Recovery their own ring-3 init payload.

| Field | Value |
| --- | --- |
| File | `chimera-ii-native-amd64.iso` |
| Size | 159119360 bytes (151 MiB) |
| SHA-256 | `82264c89159b118ad31b93296346ab6f8c66ae67add0d05a4725c93de922d602` |
| Kernel | Koronos (Multiboot2 ELF64, in-tree kbuild), no Linux kernel involved |
| Boot | GRUB 2.12 hybrid: El Torito BIOS + `efi.img` UEFI |
| Targets | `target=live`, `target=installer`, `target=recovery` (one `chimera-user-init-elf` module per entry) |
| Userspace | freestanding ELF64 init per target, high-half entry at 0x1_0000_0000 |

## Verification (2026-11-04, unchanged fail-closed verifier)

| live / bios | PASS: target=live init entered user mode and reported readiness with a consistent PID |
| live / uefi | PASS: target=live init entered user mode and reported readiness with a consistent PID |
| installer / bios | PASS: target=installer init entered user mode and reported readiness with a consistent PID |
| installer / uefi | PASS: target=installer init entered user mode and reported readiness with a consistent PID |
| recovery / bios | PASS: target=recovery init entered user mode and reported readiness with a consistent PID |
| recovery / uefi | PASS: target=recovery init entered user mode and reported readiness with a consistent PID |

Each PASS requires, in order: `[KRN ] KORONOS READY` → a CPL-3-originated
`USER INIT SYSCALL: target=<t> init_pid=<n>` → `USERSPACE READY: target=<t> init_pid=<n>`
from the user payload itself with the same PID. Traces are in `traces/`.

## What runs where

- **Live** — ring-3 text console session; prints the session banner, yields, reports ticks, exits.
- **Installer** — storage/plan dry-run report. No block backend exists in ring 3, so it writes nothing.
- **Recovery** — diagnostics report (syscall ABI self-check, tick count), exits.

The Aurora HTML desktop is *not* part of this native image; it runs in the Linux live
ISO published separately (`live-image/`). See `docs/KORONOS_VS_LINUX_7X.md` for the
subsystem-by-subsystem comparison and the deliberate non-goals.

## Fixes included

- Kernel tree synced so the ring-3 stack (address_space, physmap, frame_allocator,
  target_launch, user_entry.asm) is present and linked.
- `kernel/targets/{live,installer,recovery}_init.c` built by the kernel build script
  (`target-init-<t>.elf`) and staged into the ISO at `/boot/targets/`.
- GRUB menu graph now passes exactly one `chimera-user-init-elf` module per target.
- Readiness matcher accepts the canonical `target=<t> init_pid=<n>` form (previously
  only the legacy probe format matched, so a real payload was reported as missing).
- `init_exit` passes its exit code; initramfs packing fails loudly when `cpio` is absent.
