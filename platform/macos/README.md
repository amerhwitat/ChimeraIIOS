# macOS host integration

The Hosted edition uses a Darwin/BSD user-space bridge and native launchd, process, filesystem and desktop-opening boundaries.

- Service inspection and lifecycle: chimera-host-services with launchctl system or gui domains.
- Interface and route inspection: ifconfig and netstat.
- Static route operations from the Cisco/Junos compatibility layer use the native route utility.
- Filesystem handling must respect APFS semantics, privacy controls, sandboxing and application entitlements.
- Native Apple Clang/LLVM, NASM and CMake are the supported BareMetal build toolchain when installed.
- 32-bit macOS is not a supported target.

The adapter does not load Linux modules, replace XNU, or claim full Cocoa/AppKit, Darwin syscall or macOS application ABI equivalence.
