# Aurora userspace

Linux-style userspace for the Aurora desktop: systemd units, sysusers/tmpfiles
declarations and a DESTDIR-staged install. Ad-hoc boot scripts are not removed —
each one is wrapped by a unit, so the historical entry points keep working while
the boot order becomes declarative.

## Targets and services

| Unit | Role | Wraps |
| --- | --- | --- |
| `aurora-shell.target` | graphical shell target | — |
| `aurora-session.service` | launches the kiosk/web desktop | `bin/aurora-session` |
| `aurora-network.service` | publishes network readiness before the shell | `bin/aurora-network-wait` |
| `aurora-voiceconnect.service` | VoiceConnect transport state broker | `bin/voiceconnect-broker` |
| `aurora-profile@.service` | selects the desktop profile (`jasper`, `gates`, `aurora`, `marine`) | `bin/aurora-profile-set` |
| `jasper.target` | Windows-style shell profile | `aurora-profile@jasper` |
| `gates.target` | macOS-style shell profile | `aurora-profile@gates` |
| `aurora.target` | Linux 7.x-style shell profile | `aurora-profile@aurora` |

Profiles are data, not code: the active profile lives in `/etc/aurora/profile`
(persistent) and `/run/aurora/profile` (runtime). The kernel command line wins
only when neither file exists, e.g. `aurora.profile=jasper`.

## Usage

```sh
make check                 # unit + helper contract checks
make install DESTDIR=/tmp/stage
systemctl isolate jasper.target
```

Installed paths follow the FHS: units in `/usr/lib/systemd/system`, sysusers in
`/usr/lib/sysusers.d`, tmpfiles in `/usr/lib/tmpfiles.d`, D-Bus policy in
`/usr/share/dbus-1/system.d`, helpers in `/usr/local/bin`.

## Scope

These units describe the *Linux* live image userspace and the profile contract
shared with the native Koronos target. They do not claim that the Koronos
microkernel reaches a verified userspace handoff; that gate is tracked separately
in `docs/PRODUCTION_USERSPACE_HANDOFF.md` (OctavianOS) and the ISO acceptance
workflow.
