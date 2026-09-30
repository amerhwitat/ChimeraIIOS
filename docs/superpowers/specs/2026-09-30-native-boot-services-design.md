# Native Chimera II Boot and Enterprise Services Architecture

**Date:** 2026-09-30  
**Status:** Design specification — awaiting implementation-plan review  
**Scope:** Spit Fire, Jasper, Koronos, Kore, Aurora Installer/Desktop, service registry, recovery, ISO/Live media.

## 1. Intent

Evolve the native Chimera II OS startup and service model into a coherent firmware-to-desktop chain with capabilities users expect from modern Linux, macOS, and Windows systems while retaining a native Chimera implementation. The design must support Secure/Measured Boot where platform hardware permits it, hardware-aware driver selection, recovery modes, modular enterprise services, and installation/runtime service selection.

The target is behavioral and architectural parity of capabilities, not copying proprietary implementations or proprietary binaries.

## 2. Boot contract

The canonical boot sequence is:

```text
UEFI/BIOS -> Spit Fire -> Jasper -> Koronos early kernel -> Koronos core -> Kore -> Aurora Session -> Aurora Desktop -> user applications/services
```

Spit Fire owns firmware handoff and early platform discovery. Jasper owns boot entries, policy, recovery selection, and chain-loading. Koronos owns CPU/memory/interrupt/device initialization and exposes the hardware capability profile. Kore owns dependency-aware system service activation. Aurora owns login/session/compositor/desktop presentation.

Required boot modes:
- Normal
- Recovery
- Safe Mode
- Last Known Good
- Live Aurora
- Installer
- Diagnostics
- Other-OS chain-loader where configured

## 3. Trust model

Where supported, the boot chain records and verifies:

```text
UEFI Secure Boot -> Spit Fire -> Jasper -> Koronos -> boot modules/initramfs -> root filesystem manifest -> critical service manifests
```

Support development mode without Secure Boot, TPM 2.0 measurement when available, user-controlled trusted keys, signed kernel/modules, boot measurement records, rollback/recovery, and explicit failure diagnostics.

No proprietary Windows/macOS driver binary is copied into Chimera. External driver information may be used only for hardware identification/compatibility metadata unless redistribution rights are independently established.

## 4. Hardware capability contract

Koronos publishes a machine-readable capability profile containing CPU architecture/features, memory, GPU/display capabilities, storage, network, audio, USB/input, firmware, TPM, virtualization, power, and supported graphics APIs. Driver selection consumes hardware IDs and capability requirements in this order:

1. native Chimera driver
2. compatible open driver/metadata
3. explicitly licensed compatibility driver
4. generic safe driver

The profile is consumed by both Kore service activation and Aurora graphics/service selection.

## 5. Kore service manager

Kore becomes the native service orchestration layer. A service manifest contains an ID, type, dependencies, ordering constraints, restart policy, health checks, resource/security requirements, and optional activation triggers.

Kore must provide:
- dependency resolution
- parallel startup where dependencies allow
- deterministic ordering
- restart-on-failure policy
- health checks
- startup/shutdown ordering
- service isolation/security policy
- resource limits
- logging integration
- IPC integration
- system and per-user services
- socket/timer/event activation where implemented
- failed-service recovery and diagnostics

The compatibility goal is to provide analogous operational capabilities to systemd, Windows Service Control Manager, and launchd, without reusing their proprietary code.

## 6. Shared service registry

Installer, Kore, and Aurora consume one service registry rather than maintaining independent definitions:

```text
/etc/chimera/services/
  service-registry.json
  service-profiles.json
  dependency-graph.json
  hardware-requirements.json
  security-policies.json
```

The source-of-truth definitions will also exist in the repository for build-time validation and ISO generation.

## 7. Installer enterprise-service selection

The installer presents service profiles:

- Minimal Desktop
- Developer Workstation
- Enterprise Workstation
- Enterprise Server
- Database Server
- Web/Application Server
- File Server
- Network Server
- Virtualization Host
- Container Host
- AI/ML Workstation
- Security Workstation
- Multimedia Workstation
- Gaming
- Full Chimera Enterprise

Advanced selection exposes infrastructure, web, database, enterprise, development, AI/ML, monitoring, backup, and remote-management services. Profiles are dependency-expanded before installation and unavailable combinations are explained rather than silently enabled.

## 8. Aurora runtime service management

Aurora exposes a privileged Services center with Installed, Available, Running, Stopped, Failed, Startup, Dependencies, Logs, and Enterprise Services views. Authorized users may install/remove, start/stop/restart, enable/disable boot activation, inspect dependencies/logs, change resource limits, and roll back supported package versions.

All privileged mutations require the native authentication/authorization mechanism. The UI never bypasses Kore policy.

## 9. Recovery

Jasper and Aurora Recovery provide:

```text
Normal Boot
Safe Mode
Last Known Good
Service Recovery
Driver Recovery
Kernel Recovery
Filesystem Repair
Bootloader Repair
Secure-Boot Diagnostics
Network Recovery
Terminal
Deployment/Factory Recovery
```

A failed service or driver must be attributable in the boot journal and must not make the entire graphical system unrecoverable when a safe fallback exists.

## 10. ISO and Live integration

The Live/Installer media follows:

```text
Spit Fire -> Jasper -> Live Aurora/Installer/Recovery/Diagnostics
```

The installer composes the target installation from the base OS plus selected driver/service/profile packages. Optional enterprise services and large games remain modular and are not forced into the Live image merely because they are available.

The ISO build must validate service manifests, dependency graphs, boot artifacts, and selected package metadata before final image creation.

## 11. Compatibility boundaries

The implementation may provide import/translation tooling for Linux service units, Windows service metadata, and launchd-style service definitions where technically and legally appropriate. It must not claim binary or API compatibility that is not implemented.

ELF, PE, and Mach-O execution continue to use their respective native/compatibility/emulation layers rather than changing the native boot/service contract.

## 12. Security requirements

- Least privilege for services
- Explicit service capabilities
- No automatic installation of privileged enterprise services
- Signed package metadata where available
- Integrity checks for boot-critical files
- Secure failure behavior
- Audit trail for privileged service changes
- Recovery mode must preserve authentication boundaries except for explicitly documented offline recovery operations

## 13. Acceptance criteria

The implementation is complete only when automated and target-environment tests demonstrate:

1. Spit Fire -> Jasper -> Koronos -> Kore -> Aurora startup.
2. Normal, recovery, safe-mode, installer, Live, and diagnostics boot entries.
3. Hardware capability discovery for supported virtual/physical targets.
4. Driver selection based on the capability contract.
5. Service dependency ordering and failure recovery.
6. Installer service-profile selection and persistence.
7. Aurora runtime service management through Kore.
8. Shared registry consumed by installer, Kore, and Aurora.
9. Boot/service diagnostics sufficient to identify failed components.
10. Secure/Measured Boot paths exercised where hardware permits.
11. ISO/Live integration without requiring all optional enterprise services or games in the Live image.
12. No proprietary driver/code/assets introduced without independent redistribution rights.

## 14. Non-goals

This specification does not promise binary compatibility with Windows/macOS/Linux, does not copy proprietary bootloaders or service managers, and does not automatically redistribute proprietary drivers. It also does not require every enterprise service to be implemented in the first release; each service must have a declared implementation state and dependency contract.
