# Koronos Plug and Play and driver discovery

## Runtime discovery

Koronos enumerates PCI configuration space on x86/x86-64, including functions indicated by the function-0 multifunction header. Inventory records include BDF, vendor/device IDs, revision, class/subclass/programming interface and subsystem IDs. The current implementation uses PCI configuration mechanism #1 and requires privileged port I/O. Non-x86 hardware needs its own bus backend; this does not claim universal ACPI, USB, PCIe ECAM, I2C, SPI or platform-bus enumeration.

The driver manager selects the highest-scoring compatible registered descriptor: exact vendor/device IDs outrank subsystem-specific and class matches; class/subclass/programming-interface fields refine candidates. Bus mismatch rejects a candidate. No match remains unbound; the kernel must not create a fake driver merely to make inventory look complete.

A descriptor with no probe callback is only a metadata match. A probe callback returning zero is the driver's initialization acceptance signal, not a substitute for hardware tests. Resource allocation, interrupt routing, DMA/IOMMU policy, hotplug removal, power management, firmware loading and device-specific functionality remain driver responsibilities.

## Upstream catalog search

Run python3 tools/drivers/sync_upstream_catalog.py to download PCI/USB ID metadata from pciutils/usbutils and recursively index relevant source paths in upstream Linux, EDK II and Zephyr Git trees. The report is written to build/driver-source-index.json and ID files are cached under data/drivers/upstream/. Use --ids-only to refresh ID metadata only.

This is discovery/indexing, not an unattended driver installer. It does not fetch or execute candidate source files. Before porting source, review its license/provenance, device IDs and hardware manual, dependencies, ABI, memory model, interrupt/DMA assumptions, firmware requirements and security implications. Require reproducible builds plus positive, negative, hotplug/removal and fault-path tests before changing status beyond metadata-only.

## Mobile and microkernel contract

Mobile Edition and the microkernel consume the same catalog and matching policy. Mobile drivers still use platform-supported HAL and signing/deployment mechanisms. PCI enumeration is not applicable to many phone SoCs and must be complemented by ACPI/Device Tree and platform-bus backends.

## Validation status

Static tests validate inventory fields, selection policy, source-index safety and JSON. They do not prove PCI I/O works on physical hardware, all buses are enumerated, or a generic candidate can drive a device. Those claims require booted QEMU and named physical hardware validation.
