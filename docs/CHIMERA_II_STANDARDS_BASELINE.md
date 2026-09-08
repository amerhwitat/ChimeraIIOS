# Chimera II OS Standards Baseline

## Platform/boot

| Area | Baseline | Compatibility rule |
|---|---|---|
| Firmware | UEFI 2.11 | preferred boot contract |
| Platform tables | ACPI 6.6 | parse, validate, never assume vendor-specific extensions |
| Partitioning | GPT | default; read legacy MBR |
| Secure boot | UEFI Secure Boot + measured boot where available | optional until Chimera signing infrastructure exists |
| TPM | TPM 2.x interface | optional hardware security provider |
| Device discovery | PCI/PCIe, USB, ACPI, SMBIOS | hardware-ID based |

## Kernel/device standards

- Linux-compatible PCI device ID model for inventory and driver mapping.
- USB class/VID/PID inventory.
- NVMe over PCIe and NVMe-oF adapter boundary.
- virtio for virtualized block/network/display devices.
- IOMMU/DMAR-aware DMA isolation.
- DMA-BUF-compatible graphics/media sharing where practical.
- stable userspace ABI; no assumption of a stable Linux in-kernel module ABI.

## Storage

- GPT/ESP.
- NVMe, SATA/AHCI, SAS/HBA and virtio-block.
- mdraid, LVM2/device-mapper and hardware RAID/HBA.
- ZFS/OpenZFS optional.
- ext4 default; XFS/Btrfs optional; FAT32 ESP; interoperability modules for NTFS/exFAT.
- Windows Storage Spaces/ReFS interoperability through an adapter boundary rather than copying Windows kernel drivers.

## Graphics

`GPU → kernel driver → DRM/KMS → Mesa/Vulkan/OpenGL → Aurora → Wayland`

Fallback:

`Vulkan → OpenGL → software rendering`

Aurora should expose Wayland protocols and compatibility adapters rather than fork the Wayland protocol itself.

## Networking

- Ethernet and Wi-Fi.
- IPv4/IPv6.
- TCP/UDP/QUIC-compatible userland services.
- DNS/DHCP/NTP.
- predictable interface identity.
- optional NetworkManager/systemd-networkd adapters.
- optional OpenSSH, SMB/Samba and NFS.

## Service model

Chimera's service manager remains native. Compatibility profiles may import systemd/OpenRC-style service definitions into Chimera manifests; they do not require Chimera to become systemd.

Recommended service classes:

- `core`: boot, device manager, logging, time, entropy, IPC.
- `network`: DHCP/DNS/network configuration, SSH.
- `storage`: volume manager, RAID, filesystem manager, SMART/health.
- `desktop`: Aurora, Wayland, PipeWire, portals.
- `server`: HTTP, SMB, NFS, DNS, container runtime.
- `cognition`: knowledge ingestion, embeddings, RNN/SSM state, node exchange.

## Source baseline

- UEFI Forum: UEFI 2.11; ACPI 6.6.
- Linux kernel PCI/driver documentation.
- Linux ABI documentation.
- Linux-firmware redistribution rules.
- Ubuntu Subiquity Autoinstall storage model.
- Debian Installer firmware detection.
- FreeBSD bsdinstall, GEOM and ZFS documentation.
- Microsoft WDK, HLK, Update Catalog and Windows Server Storage documentation.
- Wayland/Weston and Mesa documentation.
- SPDK storage documentation.
- OpenZFS documentation.

The installer capability catalog is the machine-readable counterpart of this document.
