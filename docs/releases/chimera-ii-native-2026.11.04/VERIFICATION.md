# Native Koronos production verification — 2026-11-04

<badge>BLOCKED — 0/6 production cases accepted</badge>

| Target | BIOS | UEFI |
|---|---|---|
| Live | BLOCKED — no qualifying raw trace for the current immutable ISO | BLOCKED — no qualifying raw trace for the current immutable ISO |
| Installer | BLOCKED — no qualifying raw trace for the current immutable ISO | BLOCKED — no qualifying raw trace for the current immutable ISO |
| Recovery | BLOCKED — no qualifying raw trace for the current immutable ISO | BLOCKED — no qualifying raw trace for the current immutable ISO |

A valid case must use the same canonical ISO SHA-256 as the other five cases and contain, in order, kernel readiness, a syscall proven to originate at CPL3, and userspace readiness emitted by the user payload with the same nonzero kernel-assigned PID.

The previous PASS rows were withdrawn because their raw traces were not present in this evidence directory and the current exact-head full-ISO workflow did not produce the canonical ISO. A CI probe or a separately composed target ISO is diagnostic only.

Also not accepted: native VFS root publication, `/etc/os-release` OPEN/READ/CLOSE, writable `/tmp`, complete service supervision, installer persistence, Recovery repair postcondition, Aurora desktop readiness, or AP-backed SMP overlap.

No production publication is authorized.
