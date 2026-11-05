# Linux integration

Chimera II targets Linux-hosted setup/build workflows as a first-class integration environment. This layer provides source/build entry points, package-provider metadata and documentation for Debian-family, RPM-family, Arch-family, Flatpak and AppImage ecosystems.

The installer must never assume a particular Linux distribution or overwrite the host disk. Disk operations remain explicit installer actions against a selected target.

## Hosted native services and routing

The cross-platform service lifecycle adapter is tools/hosted/chimera-host-services.py; the Debian/Ubuntu package installer and systemd manager is tools/service-manager.sh. Optional FRRouting is available as the frr service and must be explicitly enabled. Route/interface operations use iproute2 on Linux. Package managers are distribution-specific; apt is not assumed on RPM/Arch systems. BareMetal builds use GCC/Clang, binutils, NASM, CMake and Ninja where present. Linux host drivers are not loaded into Koronos.
