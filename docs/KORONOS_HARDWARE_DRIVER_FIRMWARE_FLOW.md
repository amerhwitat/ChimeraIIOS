# Koronos Hardware, Driver and Firmware Flow

Koronos treats firmware and hardware discovery as prerequisites to driver activation.

## Firmware

UEFI systems expose the EFI System Table and configuration tables. Koronos consumes Multiboot2 EFI/ACPI/SMBIOS tags when supplied by the loader. The UEFI loader also reports firmware vendor/revision and the presence of ACPI and SMBIOS tables. BIOS systems are identified by the absence of EFI handoff data. UEFI exposes ACPI and SMBIOS configuration tables through the EFI System Table.

## Hardware identity

The discovery pipeline uses:

- PCI/PCIe vendor/device/subsystem/class identifiers
- USB identity and class information in the userspace scanner
- ACPI HID/CID/UID information
- SMBIOS system/baseboard/BIOS information
- UEFI device/configuration data
- storage, graphics, display and network topology

The first kernel implementation enumerates PCI devices on x86 and normalizes storage, network, display, GPU, USB and motherboard/platform classes.

## Driver selection

The order is:

1. Native Koronos driver with a matching device identity.
2. Native generic bus/class fallback.
3. Verified Linux compatibility adapter.
4. Verified Windows WDM/WDF compatibility adapter.
5. Verified macOS DriverKit compatibility adapter.
6. Generic bus fallback.
7. Unresolved-device recommendation for the installer.

A foreign .sys, .ko, KEXT or DriverKit payload is never treated as a Koronos kernel module. It is an input to the corresponding compatibility boundary.

## Runtime lifecycle

chimera_driver_probe_all enumerates hardware and binds the best available registered driver descriptor.

chimera_driver_start_all transitions matched descriptors into the active driver set and invokes a driver start/probe callback when one exists.

The existing virtual VirtIO and display registrations remain available, while PCI generic storage/network/display/GPU/platform descriptors provide deterministic fallback coverage.

## Installer recommendation

The installer records firmware type, motherboard/platform evidence, storage availability, network availability, graphics availability, PCI/USB evidence, driver selection order, foreign-driver policy, and provenance/verification policy.

The installer must not silently substitute an unverified foreign driver. A storage device required for installation must have a resolved native or verified compatibility path before committing the installation.

## Firmware security

Secure Boot is respected. Chimera does not bypass firmware security. Firmware and driver acquisition remains provenance-aware and signature/checksum aware.

## ELF artifacts

Koronos continues to boot as ELF64. The build additionally produces koronos.elf64, koronos.elf, and N-bit ELF64 containers for 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096 and 8192-bit execution widths. These N-bit artifacts carry a Chimera execution-width note. Widths beyond the physical CPU width are execution-layer modes rather than claims of native hardware instruction width.
