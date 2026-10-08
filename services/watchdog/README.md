# Chimera II Watchdog
Common userspace watchdog supervisor for Koronos, the microkernel runtime, and Mobile Edition.

Detection and recovery are separated. Koronos exposes the watchdog ABI, its timer path calls the tick function, and userspace adapters publish monotonic heartbeat timestamps under /run/chimera/watchdog/heartbeats. A stale heartbeat creates a recovery request under /run/chimera/watchdog/recovery. Kore or the edition-specific supervisor owns the privileged restart operation.

The watchdog never executes arbitrary commands from heartbeat payloads. The same protocol is used on desktop Koronos and ARM64 Mobile Edition; only the boot/device adapter and recovery owner differ.

Adapters arm a service with `chimera-watchdog --heartbeat <service-id>`; the command writes a monotonic timestamp atomically. Missing heartbeat files remain unarmed rather than failed.
