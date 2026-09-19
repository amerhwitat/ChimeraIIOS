# Chimera II Hardware / Driver Compatibility Layer

This directory is the capability registry, driver adapter boundary, secure acquisition layer, and Aurora hardware-management backend.

## Coverage

CPU/SoC, GPU, PCI/PCIe, USB, NVMe/SATA/SCSI, virtio, I2C/SPI/GPIO, networking, audio, camera, input, display, printing, and virtual devices are represented through capability metadata and adapters.

## Aurora scanner

Run:
python3 drivers/aurora_hardware_scanner.py --json

The scanner inventories Linux (/sys, /proc, PCI/USB), Windows PnP/PowerShell, and macOS system_profiler/ioreg. It creates a local remediation plan but does not silently install anything.

## Secure acquisition

The lifecycle is:
discover -> identify -> resolve official source -> verify license -> verify signature -> verify hash -> quarantine -> stage -> explicit approval -> install -> health-test -> rollback.

Sources are restricted to declared official vendor, OS, distribution, or documented upstream locations. Arbitrary installer scripts, unsigned artifacts, hash mismatches, unknown licenses, and untrusted packages are rejected.

## Compatibility

Linux can use a native Chimera driver ABI or signed distribution modules. Windows .sys packages and macOS kernel extensions are not directly loaded by Koronos; they are handled through native-platform, VM, Wine, WSL, or virtual-device compatibility boundaries as appropriate.

See aurora_driver_policy.json and security/koronos_security_policy.json for enforcement contracts.
