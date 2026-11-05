# Linux service management

Chimera uses systemd as its current Linux service backend and keeps the service catalog declarative. The manager deliberately separates package installation from service activation.

## Commands

- `chimera-services list` — list catalogued units and their active/enabled state.
- `chimera-services status [id]` — inspect one or all services.
- `sudo chimera-services install <id>` — install the mapped Ubuntu/Debian package only.
- `sudo chimera-services profile <name>` — install packages in a named profile.
- `sudo chimera-services enable-now <id>` — explicitly enable and start one unit.
- `sudo chimera-services disable-now <id>` — stop and disable one unit.

Profiles: `base`, `desktop`, `network`, `server`, `storage`, `security`, and `developer`.

## Default policy

The catalog currently describes 55 Linux service integrations, including journaling, udev, logind, D-Bus, cron, networking, printing, Bluetooth, audio, storage, security, directory identity, web/mail/DNS servers, databases, containers, remote administration and monitoring. The minimal default set is journaling, device management, the system message bus and scheduled jobs. Desktop, server, developer, identity, storage and network services remain installable options. Aurora Settings declares Linux Services, Optional Services and Service Profiles pages backed by this catalog; privileged lifecycle actions are routed through the service manager and are subject to the Koronos/Aegis elevation policy.

Installing a profile installs packages only. It does not enable or start the services. In particular, SSH, SMB/Samba, WS-Discovery, Avahi, NFS, web servers, databases, directory clients and container daemons require explicit administrator activation. Firewall policy and network exposure must be reviewed before enabling listeners.

The catalog maps package names and systemd unit names for Ubuntu 24.04. A missing unit is reported by systemd rather than silently replaced with a guessed unit. Some desktop services are user-session services and are not managed by this system-wide command; PipeWire is catalogued as informational until a session-aware adapter is available.

## Future backends

The JSON service registry remains the platform-neutral capability contract. This Linux manager is an adapter, not a replacement for Koronos service control. Windows SCM and macOS launchd adapters can implement the same operations. Kernel-owned services must not be manipulated directly by this tool.
