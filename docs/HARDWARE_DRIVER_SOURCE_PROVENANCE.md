# Hardware / Driver Source Provenance

The driver architecture was informed by public documentation and open-source ecosystems including:

- Linux kernel driver/device model: https://www.kernel.org/
- Linux kernel documentation: https://docs.kernel.org/
- Mesa graphics stack: https://docs.mesa3d.org/
- freedesktop hardware data: https://github.com/freedesktop/hwdata
- Microsoft Windows Driver Kit documentation: https://learn.microsoft.com/windows-hardware/drivers/
- CUPS/OpenPrinting: https://openprinting.github.io/cups/
- SANE: https://www.sane-project.org/

These sources define interfaces, protocols, architecture and compatibility concepts. Chimera II does not copy proprietary Windows driver binaries or indiscriminately vendor third-party source. When a future adapter incorporates a compatible open-source driver, its license, copyright and source provenance must remain attached to that component.

The hardware registry intentionally stores family/class capabilities and supports generated ID data. This avoids pretending a static hand-maintained list can contain every historical and future PCI/USB model.
