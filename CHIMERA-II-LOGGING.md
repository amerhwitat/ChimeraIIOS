# Chimera II Logging and Event Subsystem

Chimera II provides a native logging and event architecture.

## Log locations

- `/var/log/system.log`
- `/var/log/kernel.log`
- `/var/log/boot.log`
- `/var/log/service.log`
- `/var/log/security.log`
- `/var/log/hardware.log`
- `/var/log/network.log`
- `/var/log/package.log`
- `/var/log/update.log`
- `/var/log/audit.log`
- `/var/log/events/events.log`
- `/var/log/events/events.jsonl`

## Persistent journal

Structured journal data is stored under:

`/var/lib/chimera/journal/`

## Crash/panic data

Kernel crash/panic information is stored under:

`/var/lib/chimera/crash/`

## Rotation

Logs support:

- size-based rotation
- daily rotation
- configurable retention
- compression
- per-subsystem limits

## Event levels

- TRACE
- DEBUG
- INFO
- NOTICE
- WARNING
- ERROR
- CRITICAL
- ALERT
- EMERGENCY

## Core event classes

- boot
- kernel
- hardware
- storage
- network
- service
- security
- audit
- package
- update
- panic/crash

Logging failure must never be allowed to crash Koronos or a critical system service.
