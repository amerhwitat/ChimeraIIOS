# Chimera II OS — native Koronos ISO chimera-ii-native-2026.11.05

Hybrid BIOS+UEFI image that boots the Koronos microkernel (Multiboot2, no Linux kernel) and hands
Live, Installer and Recovery their own ring-3 init payload, with the embedded AI knowledge database staged.

| Field | Value |
| --- | --- |
| File | `chimera-ii-native-amd64.iso` |
| Size | 159342592 bytes (151 MiB) |
| SHA-256 | `cba147b488a2176a7bb92734901551f2866897af758eabc5a028e8d3dd5d2a24` |
| Kernel | Koronos (in-tree kbuild), Multiboot2 ELF64 |
| Boot | GRUB 2.12 hybrid: El Torito BIOS + `efi.img` UEFI |
| Targets | `target=live`, `target=installer`, `target=recovery` |
| Knowledge DB | `/boot/ai/knowledge-db.json` — 269 entries |

## Boot trace contract

`[KRN ] KORONOS READY` → `[AI  ] Knowledge database staged: N entries, M bytes` →
`USER INIT SYSCALL: target=<t> init_pid=<n>` (CPL-3 proof) → `USERSPACE READY: target=<t> init_pid=<n>`
emitted by the payload itself. Traces in `traces/`, one per target and firmware.

## Verification (unchanged fail-closed verifier)

| Case | READY markers | Verifier |
| --- | --- | --- |
| live / bios | 1 | PASS: target=live init entered user mode and reported readiness with a consistent PID |
| live / uefi | 1 | PASS: target=live init entered user mode and reported readiness with a consistent PID |
| installer / bios | 1 | PASS: target=installer init entered user mode and reported readiness with a consistent PID |
| installer / uefi | 1 | PASS: target=installer init entered user mode and reported readiness with a consistent PID |
| recovery / bios | 1 | PASS: target=recovery init entered user mode and reported readiness with a consistent PID |
| recovery / uefi | 1 | PASS: target=recovery init entered user mode and reported readiness with a consistent PID |

## What each target does

- **Live** — ring-3 text console session: banner, yield, tick count, exit.
- **Installer** — storage/plan dry-run report; no block backend exists in ring 3, so it writes nothing.
- **Recovery** — diagnostics report (syscall ABI self-check, ticks), exit.

The Aurora HTML desktop ships in the Linux live ISO, not in this native image.
See `docs/KORONOS_VS_LINUX_7X.md` (subsystem map vs Linux 7.3) and `docs/KNOWLEDGE_DB.md`.
