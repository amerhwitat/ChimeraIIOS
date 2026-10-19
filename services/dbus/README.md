# Koronos D-Bus status service

This package provides a real D-Bus service endpoint for the hosted Linux
editions of ChimeraIIOS and OctavianOS. It is **not** a D-Bus broker/daemon and
does not pretend to supply missing kernel IPC primitives. It requires a system
bus (`dbus-daemon` or compatible broker), Python 3, and `dbus-next`.

## Interface

- Chimera bus name: `org.chimera.OS`; object path `/org/chimera/OS`.
- Octavian bus name: `org.octavian.OS`; object path `/org/octavian/OS`.
- Methods: `Ping() -> s`, `GetStatus() -> JSON string`, and
  `ListServices() -> JSON string`.
- API is read-only: no arbitrary command or privileged mutation methods.
- The process stays alive for PID 1/service-manager supervision.

## Hosted Linux install

Install `dbus-next` from the distribution repository; install the script to
`/usr/libexec/<os>/chimera_dbus_service.py`, the unit under
`/usr/lib/systemd/system`, policy under `/etc/dbus-1/system.d`, and activation
under `/usr/share/dbus-1/system-services`. Enable the matching unit. The SysV
wrapper delegates to the same unit.

## Native Koronos limitation

A service file cannot run in the freestanding ISO by itself. Native production
use still requires kernel IPC/AF_UNIX transport, credential and policy
enforcement, process lifecycle, target-specific native `koronos-init`, and
the unchanged six-case BIOS/UEFI userspace acceptance gate. This package does
not claim those facilities or production boot gates are complete.
