# Koronos Service Init Contract (KSO)

Status: **design/implementation contract only — not a production runtime implementation**. This document names the intended services and fixes the compatibility/security contract. Production userspace acceptance remains blocked until the native init, service manager, syscall/process lifecycle, ISO staging, and six-case QEMU acceptance are implemented and verified.

## Architecture

The kernel's only job at this boundary is to establish protected process execution and launch exactly one target-selected native ELF init. Userspace then owns dependency ordering and service supervision through **Koronos Service Orchestrator (KSO)**. KSO supports:
- systemd-style unit files with `Description`, `Requires`, `After`, `Wants`, `ExecStart`, `ExecStop`, `Restart`, and target dependencies;
- System V compatibility scripts at `/etc/init.d/<service>` with `start|stop|restart|status`, plus runlevel links under `/etc/rcN.d/SNN*` and `KNN*`;
- deterministic target selection. Exactly one of `target=live`, `target=installer`, or `target=recovery` must be selected. Never fall back from a missing target init to a smoke-test ELF.

## Canonical service names

| Unit | Responsibility | Start condition |
|---|---|---|
| `koronos-init.service` | PID 1 init contract and KSO handoff | Kernel has admitted target-specific native init |
| `koronos-service-orchestrator.service` | Dependency ordering, service supervision, SysV compatibility | Core init facilities available |
| `chimera-devd.service` | Device discovery and driver-event dispatch | Kernel device/event interface available |
| `chimera-logd.service` | System log collection and rotation | Console and log storage available |
| `chimera-accountd.service` | Account, group, and session policy | Root filesystem and account database available |
| `chimera-networkd.service` | Network configuration | Runlevel 3 or target requests networking |
| `chimera-displayd.service` | Display/session handoff | Graphics stack available |
| `aurora-session.service` | Aurora Wayland Glass Desktop | Live target, runlevel 5, display service ready |
| `chimera-installer.service` | Actual install, verification, and reboot workflow | Installer target only |
| `chimera-recovery.service` | Actual filesystem/system repair workflow | Recovery target only |

A service name or unit file is not proof the service is executable or started.

## Runlevels

- `0`: halt; stop services in reverse dependency order.
- `1`: single-user rescue; minimal services, no network by default.
- `2`: multi-user local services.
- `3`: multi-user with networking.
- `4`: site/OEM-defined; no implicit privilege escalation.
- `5`: graphical session; Aurora is enabled only for the Live target.
- `6`: reboot; stop services in reverse dependency order.

Installer and Recovery are boot targets, not aliases for graphical runlevel 5. The command line and staged module must agree; mismatch is a hard failure.

## User and privilege levels

- **L0 — Kernel/Supervisor:** ring 0; kernel-owned memory and device authority.
- **L1 — System service:** ring 3, dedicated service identity/capabilities; no general administrator authority by default.
- **L2 — Administrator:** ring 3, authenticated account with explicit administrative authorization.
- **L3 — Standard user:** ring 3, per-user session and least privilege.
- **L4 — Restricted/guest:** ring 3, sandboxed session and no administrative capabilities.

These are policy labels, not CPU privilege rings. All userspace code runs at CPL3. Runlevel selection must never elevate a process. Every transition requires kernel-enforced identity, capability, address-space, and syscall checks.

## Required implementation gates (must be closed before production acceptance)

1. Build a freestanding, target-aware native `koronos-init` ELF and KSO runtime; do not substitute the current smoke-test ELF.
2. Implement a real process lifecycle and required kernel ABI: process creation/exec, wait/reap, signals/termination, file and directory operations, mount/initramfs access, environment/argv, credentials/capabilities, and service status. Existing syscall names alone do not prove those operations work.
3. Keep PID 1 alive while it supervises children; kernel launch must not treat a successful one-shot readiness probe as a complete service manager.
4. Stage exactly one matching native init module for each Live/Installer/Recovery ISO target; reject missing, duplicate, mismatched, or unbounded modules.
5. Add host unit tests for unit parsing, dependency ordering/cycle rejection, SysV action compatibility, runlevel mapping, and privilege policy.
6. Run all six independent BIOS/UEFI production boots using the unchanged verifier. Each must show a genuine CPL3-originated syscall acknowledgement and matching kernel-owned nonzero PID marker from the actual init.
7. Separately verify Live-to-Aurora, installer write/verify/reboot/installed boot, a real Recovery repair, and AP-backed concurrent SMP. A green build or six boot prompts alone is insufficient.

## Acceptance rule

Until all seven gates are evidenced, report production acceptance as **BLOCKED**. Never fabricate readiness markers, weaken the verifier, or promote a test probe to production init.
