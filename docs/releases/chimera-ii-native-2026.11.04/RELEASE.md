# Chimera II OS — native Koronos engineering candidate (2026-11-04)

**Status: BLOCKED — not a production release.**

This directory records the intended native Koronos BIOS/UEFI image contract. It is not proof that a releasable ISO exists or that its six target/firmware cases passed.

## Artifact identity

| Field | Status |
|---|---|
| Intended image | `chimera-ii-native-amd64.iso` |
| Candidate SHA-256 previously listed | Withdrawn pending artifact verification |
| Current exact-head ISO | Not established; the latest full-ISO workflow failed before producing the canonical ISO |
| Boot chain | GRUB BIOS/UEFI → Koronos ELF64 |
| Target payloads | Live, Installer and Recovery freestanding init ELF sources exist |

The previous SHA-256 entry is not retained as a verified checksum because the corresponding ISO bytes and raw six-case traces are not available in the checked-in evidence directory.

## Verification status

**0/6 production cases accepted.** The previous six PASS statements are withdrawn. The current release gate requires six independent boots of one immutable ISO SHA-256 and raw traces proving the same sequence in each case:

`[KRN ] KORONOS READY` → CPL3-originated `USER INIT SYSCALL` → matching nonzero-PID `USERSPACE READY`.

No checked-in raw traces currently substantiate the earlier six PASS claims. The latest full-ISO CI run failed in the SDK build before producing the canonical ISO; its userspace and six-case checks correctly remained blocked.

## What the current target payloads do

- **Live:** ring-3 text-console diagnostic; no native desktop session.
- **Installer:** storage-plan dry run; no block-device writes or persistent installation.
- **Recovery:** diagnostic report; no repair operation or verified repair postcondition.

The kernel source contains a single-init CR3/ring-3 launch path and DPL3 syscall acknowledgement logic. Source presence and unit tests do not replace successful target boot traces. The process record remains a limited single-init lifecycle, not a general process/task implementation.

## Remaining release blockers

1. Rebuild the SDK and canonical ISO at one exact commit; inspect the embedded manifests and boot artifacts.
2. Produce raw Live/Installer/Recovery × BIOS/UEFI traces against that same ISO SHA-256.
3. Integrate a real kernel VFS, initramfs root publication, descriptor table and OPEN/READ/WRITE/CLOSE/SEEK semantics with user-pointer validation.
4. Implement complete process/task lifecycle and service supervision.
5. Implement AP startup, per-CPU scheduling and measured concurrent execution on at least two CPUs.
6. Verify desktop health, installer persistence after cold reboot, and Recovery repair postconditions.

**Publication rule:** keep this candidate unreleased until every required gate passes. Do not infer a pass from source code, host tests, a kernel-only boot, separately repacked diagnostic images, or a generated status document.
