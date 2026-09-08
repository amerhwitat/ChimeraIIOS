# Chimera II OS Standards Baseline

**Baseline revision: 2026-09**

## Platform / boot

| Area | Current baseline | Chimera rule |
|---|---|---|
| Firmware | UEFI 2.11 | preferred native boot contract |
| Platform tables | ACPI 6.6 | parse/validate; isolate vendor extensions |
| Partitioning | GPT + ESP | default; legacy MBR is compatibility-only |
| Secure boot | UEFI Secure Boot | signed image policy; measured boot where available |
| TPM | TPM 2.x | optional provider, mandatory abstraction |
| Device discovery | PCI/PCIe, USB, ACPI, SMBIOS | hardware-ID based discovery |

UEFI Forum currently lists UEFI 2.11 and ACPI 6.6 as the latest published UEFI/ACPI specifications. citeturn0search2

## Kernel / driver / I/O

- Stable Chimera userspace ABI; no dependency on a stable Linux in-kernel ABI.
- PCI lifecycle: discover → match → enable → BAR map → interrupt → DMA domain → runtime → quiesce.
- DMA mappings must use explicit ownership tokens and paired unmap operations.
- IOMMU-aware device address spaces; evolve toward an IOMMUFD-like capability model.
- DMA-BUF-style buffer sharing for graphics/media where applicable.
- virtio boundaries for virtual block/network/display devices.
- PCI P2P DMA must be topology and isolation aware.

Linux's current driver documentation covers PCI support, P2P DMA, DMA mapping, IOMMUFD/VFIO and device I/O; these are interoperability references, not source-code dependencies. citeturn1search0turn1search2turn1search4turn1search8

## Storage

- GPT/ESP.
- NVMe, SATA/AHCI, SAS/HBA and virtio-block adapter boundaries.
- mdraid, LVM2/device-mapper and hardware RAID/HBA adapters.
- OpenZFS optional.
- ext4 default; XFS/Btrfs optional; FAT32 ESP; NTFS/exFAT interoperability modules.
- Windows Storage Spaces/ReFS interoperability through external adapter boundaries.
- Durable filesystem work must define crash-consistency, journal/WAL recovery, checksums and snapshot semantics.

## Graphics

`GPU → device driver → memory/buffer manager → Vulkan/OpenGL → Aurora → Wayland`

Fallback:

`Vulkan → OpenGL → software renderer`

Aurora must implement the Wayland protocol model rather than fork it. Wayland uses an asynchronous object/message model and XML protocol definitions. citeturn2search0turn2search8

The 2026 protocol baseline is Wayland protocols 1.49. citeturn2search3

The current Khronos Vulkan documentation snapshot is Vulkan 1.4.361 (generated 2026-09-03). citeturn1search3

Priority graphics interfaces:

- `wl_display`, `wl_registry`, `wl_compositor`, `wl_surface`;
- xdg-shell;
- linux-dmabuf;
- presentation timing;
- input seats, pointer, keyboard and touch;
- Vulkan swapchain/presentation;
- PipeWire media integration.

## Networking

- Ethernet and Wi-Fi adapter boundaries.
- IPv4/IPv6 dual-stack, IPv6 preferred when policy permits.
- ARP/NDP, ICMP/ICMPv6, UDP, TCP.
- QUIC-compatible service boundary.
- DNS, DHCP/DHCPv6, NTP/PTP as services.
- predictable interface identity.
- zero-copy packet ownership with explicit DMA lifetime.
- Happy Eyeballs v2 for dual-stack connection establishment. RFC 8305 specifies asynchronous resolution, address ordering and racing connection attempts while preferring IPv6. citeturn2search6turn2search7

## Service model

Chimera's service manager remains native. Compatibility profiles may import systemd/OpenRC-style definitions into Chimera manifests; Chimera does not become systemd.

Recommended service classes:

- `core`: boot, device manager, logging, time, entropy, IPC.
- `network`: DHCP/DNS/network configuration, SSH.
- `storage`: volume manager, RAID, filesystem manager, health.
- `desktop`: Aurora, Wayland, PipeWire, portals.
- `server`: HTTP, SMB, NFS, DNS, container runtime.
- `cognition`: knowledge ingestion, embeddings, recurrent/SSM state and 128D node exchange.

## Security

Required invariants:

- Secure/measured boot where platform support exists;
- W^X for executable user mappings;
- capability-checked syscalls;
- protected MMIO;
- IOMMU/DMA isolation;
- explicit packet/buffer ownership;
- least-privilege services;
- signed modules and manifests;
- audit event IDs;
- key rotation/revocation;
- reproducible build metadata;
- fuzzing of instruction, filesystem, firmware and network parsers.

## Compatibility

- x86-64 and ARM64 host execution first.
- R8192/C8192 remains an experimental virtual architecture until FPGA/silicon evidence exists.
- POSIX-like and Windows compatibility are subsystem boundaries, not claims of binary compatibility until conformance tests exist.
- Wine/CEF integration must preserve license/provenance boundaries.

## Source baseline

- UEFI Forum: UEFI 2.11 / ACPI 6.6. citeturn0search2
- Linux PCI/driver/DMA/IOMMUFD documentation. citeturn1search0turn1search1turn1search2turn1search4
- Wayland and wayland-protocols. citeturn2search0turn2search3
- Khronos Vulkan documentation/registry. citeturn1search3turn1search16
- IETF RFC 8305 for Happy Eyeballs v2. citeturn2search6
- Existing project references for GPT/ESP, virtio, NVMe, OpenZFS and POSIX interoperability.

All third-party code incorporated into Chimera must record license, version, provenance and compatibility impact. Standards may be implemented; arbitrary external kernel source must not be copied into the clean-room codebase.
