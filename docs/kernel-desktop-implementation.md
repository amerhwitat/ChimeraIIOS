# Chimera II OS kernel/desktop implementation

This document turns the parity inventory into native Chimera contracts. The goal is functional interoperability with documented interfaces and open standards, not source-level cloning of Linux, Windows, or Apple operating systems.

## Kernel layers

1. **Koronos core** — boot, CPU discovery, SMP scheduling, timers, IPC, object lifetime and service orchestration.
2. **Platform feature registry** — a single capability snapshot for memory, I/O, security, networking, display and power subsystems.
3. **Device/driver layer** — PCI discovery, class matching, native drivers, and compatibility adapters.
4. **Memory/VFS/I/O contracts** — page/cache/VFS/block interfaces are represented by stable native ABI hooks so architecture-specific implementations can be added without changing Aurora or compatibility clients.
5. **Network/security contracts** — socket endpoints and capability checks are available to the kernel and future Spotnik providers.
6. **Graphics/power contracts** — display targets and power state are registered through the same platform layer used by Aurora.
7. **Diagnostics** — platform snapshots expose feature/state counts for boot diagnostics and support tooling.

The platform registry is intentionally bounded and freestanding-safe for early boot. It is not a general-purpose heap or full VM/VFS implementation; architecture-specific allocators, filesystems, network transports and GPU drivers can replace the registry-backed fallbacks incrementally.

## Aurora

Aurora consumes the same platform capability model. Its target feature set covers a Wayland-native compositor, DRM/KMS display path, multi-monitor/HiDPI handling, input and accessibility, media, emulation windows, compatibility facades and RTL/LTR internationalization.

## Compatibility rule

Linux, Windows and Darwin are used as documented architectural references. Linux's driver model emphasizes a common device/bus model and probing/hotplug; Windows documents object, memory, process/thread, I/O, PnP, power and security managers; XNU combines Mach, BSD and IOKit. These are architectural references, not copied implementations.

## Enablement

A feature should be marked ready only after its native provider is present, probing/fallback works, diagnostics expose its state, and a regression test covers the contract. ISO staging can ship the contracts and configs even when a hardware-specific provider is unavailable.
