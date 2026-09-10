# Linux integration

Chimera II targets Linux-hosted setup/build workflows as a first-class integration environment. This layer provides source/build entry points, package-provider metadata and documentation for Debian-family, RPM-family, Arch-family, Flatpak and AppImage ecosystems.

The installer must never assume a particular Linux distribution or overwrite the host disk. Disk operations remain explicit installer actions against a selected target.
