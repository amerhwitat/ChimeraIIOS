# Hardware / Driver Source Provenance

The driver architecture and acquisition layer are informed by public documentation and open-source ecosystems including:

- Linux kernel driver/device model: https://www.kernel.org/
- Linux kernel documentation: https://docs.kernel.org/
- Linux kernel source: https://github.com/torvalds/linux
- Mesa graphics stack: https://docs.mesa3d.org/
- freedesktop hardware data: https://github.com/freedesktop/hwdata
- Microsoft Windows Driver Kit documentation: https://learn.microsoft.com/windows-hardware/drivers/
- Microsoft Driver Store documentation: https://learn.microsoft.com/en-us/windows-hardware/drivers/install/driver-store
- CUPS/OpenPrinting: https://openprinting.github.io/cups/
- SANE: https://www.sane-project.org/

## Acquisition policy

Chimera II uses these sources as provenance and discovery references, not as permission to redistribute arbitrary binaries. The acquisition broker requires HTTPS, source allowlisting, hardware matching, SHA-256 verification, trust/signature validation, and explicit staging.

Linux kernel modules remain kernel-ABI specific. Windows packages remain subject to INF/catalog/signature and Driver Store requirements. Chimera does not bypass platform security or disable Secure Boot/test-signing enforcement to make a package load.

These sources define interfaces, protocols, architecture and compatibility concepts. When a future adapter incorporates compatible open-source driver source, its SPDX license, copyright and source provenance remain attached to that component.

The hardware registry intentionally stores family/class capabilities and supports generated ID data. This avoids pretending a static hand-maintained list can contain every historical and future PCI/USB model.
