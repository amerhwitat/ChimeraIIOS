# Windows/Linux service parity and integration register

Status: **implementation worklist; not a claim that these services are implemented or running**.
Release status remains BLOCKED until target-specific runtime evidence passes the unchanged production DAPS.

## Porting rule

Port service contracts and required behavior, not Windows/Linux binaries or assumptions about their kernel APIs. Every service must be implemented against Koronos' own VFS, process, device, IPC, security and timer interfaces; have an explicit target manifest and dependencies; be spawned and reaped by the production process backend; expose a real health probe; and have a failure/restart/shutdown test. A catalog entry, compiled object, fake-backend test, or registration is not a running service.

## Core service families to inventory and port

| Family | Windows examples | Linux examples | Required Chimera/Octavian contract | Current acceptance |
|---|---|---|---|---|
| Init / service supervision | Service Control Manager | systemd or OpenRC | process spawn, owned PID/handle, health, exit wait/reap, bounded restart/backoff, dependency order, reverse shutdown | Supervisor API/test exists; production process backend not wired |
| Logging / event journal | Windows Event Log | journald, syslog | bounded event transport, persistent sink when available, severity, rotation/overflow policy | Not production-verified |
| Device discovery / PnP | Plug and Play, device installation | udev, devtmpfs | enumerate actual buses/devices, driver probe/bind/unbind, hotplug event and device-node ownership | Not production-verified |
| Storage / volume management | Storage Service, Virtual Disk | udisks, mount units, device-mapper services | block discovery, geometry and flush, partition/filesystem detection, mount/unmount, sync and error reporting | Production block discovery/mount not established |
| IPC / name service | RPC Endpoint Mapper, COM activation | D-Bus, Unix sockets | authenticated endpoint registry, bounded messages, peer identity, timeout/cancellation | Not production-verified |
| Network configuration | DHCP Client, DNS Client, WLAN AutoConfig | NetworkManager, systemd-networkd, systemd-resolved | NIC driver, link state, DHCP, DNS cache/resolver, route updates, privilege separation | Not production-verified |
| Time synchronization | Windows Time | chrony, systemd-timesyncd | monotonic/realtime clock contract, authenticated time sources where configured, bounded correction | Not production-verified |
| Identity / authorization | Local Security Authority, SAM, Windows Defender components | PAM, NSS, polkit | credentials, capability checks, policy evaluation, audit trail; no direct reuse of incompatible OS security internals | Not production-verified |
| Update / package lifecycle | Windows Update, BITS, MSI service | package managers, unattended-upgrades | signed/hash-verified packages, transactional staging/rollback, dependency graph, durable commit | Not production-verified |
| Scheduled work | Task Scheduler | cron, atd, systemd timers | persistent schedule definitions, missed-run policy, cancellation and bounded concurrency | Not production-verified |
| Remote access | OpenSSH for Windows, Remote Desktop services | sshd, remote desktop daemons | opt-in network listener, authentication, authorization, audit, secure defaults | Not production-verified |
| Printing / discovery | Print Spooler | CUPS, Avahi | device discovery, queued jobs, bounded spool storage, access control | Not production-verified |
| Power / session | Power service, User Profile Service | logind, upower, display/session managers | suspend/reboot/shutdown coordination, user/session lifecycle, device quiesce | Not production-verified |
| Graphics / desktop | DWM, Winlogon, Userinit, Explorer | display manager, compositor, desktop session | framebuffer/display discovery, input service, compositor start, session handshake and clean logout | Aurora/Marine handoff not proven |
| Security monitoring | Microsoft Defender services, Firewall services | auditd, firewall and endpoint security daemons | policy-enforced event collection, firewall/device hooks, fail-closed health state | Not production-verified |
| Diagnostics / recovery | Windows Recovery Environment services | initramfs, rescue targets, fsck services | bounded repair transaction, before/after evidence, verified postcondition | Recovery transaction not proven |

This is a service-family inventory, not an assertion that every Windows SKU or Linux distribution has the same services. Optional, vendor-specific, licensed, hardware-dependent and user-installed services require separate compatibility and security review.

## Required target manifests

Manifests must be separate for Live, Installer, Recovery, and the installed desktop. They must name exact service IDs, executable/module paths, dependencies, criticality, health timeouts, restart policy and shutdown order. Optional network, printing, discovery and remote-access services must not be critical to boot unless the selected edition explicitly requires them.

- **Live/Aurora (and Octavian Marine where selected):** filesystem/VFS, device manager, process manager, logging, IPC, display/input stack, compositor and session; ready only after the real session handshake.
- **Installer:** device discovery, block I/O, partition/filesystem support, installer namespace, durable sync, reboot coordination; acceptance requires install → cold reboot → persistent readback and installed-system boot.
- **Recovery:** read-only discovery first, explicit authorization for writes, bounded transaction journal, rollback/repair, verified before/after state; a shell alone is not success.
- **All targets:** supervisor, timer/clock, console/diagnostics and security boundary; service failures must propagate according to declared criticality.

## Build and evidence gates

1. Maintain one reviewed service ID/contract registry and edition-specific manifests in both repositories; avoid silent vendor-only patches that are removed by canonical-source synchronization.
2. Compile every implementation against the real kernel/user ABI with warnings treated as errors and run deterministic unit tests.
3. Exercise the same manifest through the production spawn/wait/reap backend; fake backends are regression tests only.
4. Test start ordering, dependency failure cascade, failed health probes, child exit, restart limit/backoff, stop/reap errors, reverse shutdown, PID reuse, timeout and resource exhaustion.
5. Capture real target traces and bind them to the exact final ISO SHA-256. Pass Live/Installer/Recovery × BIOS/UEFI through the unchanged fail-closed DAPS verifier.
6. Separately prove Aurora/Marine session launch, installer cold-reboot persistence, recovery postconditions and overlapping work on at least two distinct AP-started CPU IDs.
7. Publish only after all gates pass. Missing evidence remains NOT RUN/FAIL; it must never be converted to PASS by a catalog, probe ELF, static marker or mock.

## Immediate implementation blocker

The current supervisor API has callbacks for start/probe/wait-exit/stop, but the production process model is still a synchronous single-init launch with a single active target/PID/address-space context. Until process-owned execution contexts, scheduler integration, safe spawn/wait/exit/reap syscalls and a production backend exist, wiring these callbacks to the current target launcher would not create a real multi-process service system and could corrupt target ownership. Do not claim the service catalog is integrated as running daemons until that architecture and its runtime evidence are complete.
