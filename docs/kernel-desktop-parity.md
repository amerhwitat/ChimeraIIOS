# Chimera II OS cross-platform feature parity

Koronos and Aurora now have a maintained parity inventory covering Linux, Windows and Darwin/XNU feature families. Linux documents scheduler, memory, power, timers, storage, networking, GPU, input, audio, USB, PCI, security and virtualization subsystems. Windows documents object, memory, process/thread, I/O, Plug and Play, power, configuration and security managers. XNU combines Mach, BSD and IOKit with platform, security, syscall, driver and test infrastructure.

The inventory is an implementation target, not copied source code. Compatibility facades are allowed, while proprietary implementation code remains excluded.

Each subsystem is intended to have native Chimera APIs, capability probing, graceful fallback, diagnostics and tests before release-ISO enablement.
