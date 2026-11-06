# Chimera II OS — native Koronos ISO chimera-ii-native-2026.11.06

| Field | Value |
| --- | --- |
| File | `chimera-ii-native-amd64.iso` |
| Size | 192880640 bytes (183 MiB) |
| SHA-256 | `725f4e84344b4a39028f2e5f0603842437ccc859bc6d45c1441328dade4526e0` |
| Kernel | Koronos (Multiboot2 ELF64) + 373-entry embedded knowledge database |
| Boot | GRUB 2.12 hybrid BIOS + UEFI, menu waits 300 s for input |
| Targets | Live, Installer, Recovery (ring-3 init each) |
| Payload | media 57, apps 153, docs 278, CI workflows 83, catalogues 123 files |

## Menu behaviour
Primary menus (GRUB, Jasper, Spit Fire, Installation) now hold for **300 s** with a visible countdown;
sub-menus (recovery, safe mode, last-known-good, services) hold 120 s. Verified on serial:
`automatically in 300s` … `298s` with the kernel not starting.

Two real config bugs were fixed to make that true: GRUB script has no `||` operator and no `&&`
chains, so the previous config aborted while parsing and GRUB booted the default entry in ~7 s.

## Verification (2026-11-06, unchanged fail-closed verifier)
| target | BIOS | UEFI |
| --- | --- | --- |
| live | PASS | PASS |
| installer | PASS | PASS |
| recovery | PASS | PASS |

Traces in `traces/`. Each PASS: `[KRN ] KORONOS READY` → `[AI  ] Knowledge database staged: 373 entries`
→ CPL-3 `USER INIT SYSCALL` → `USERSPACE READY: target=<t> init_pid=<n>`.
