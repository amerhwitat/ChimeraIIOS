# Chimera II OS Installer, Hardware Compatibility, and Optional Services

## 1. Design target

Chimera II uses a **Wayland-first, UEFI-first, hardware-adaptive installer**. The installer has two layers:

1. **Planner/inventory layer**: safe, repeatable, non-destructive by default.
2. **Privileged adapters**: platform-specific operations that require explicit confirmation.

This deliberately follows proven installer patterns from Ubuntu Autoinstall, Debian Installer, FreeBSD bsdinstall, and Windows setup/storage tooling while keeping Chimera II's kernel and service architecture independent.

Ubuntu Autoinstall currently supports direct, LVM, ZFS and hybrid/TPM-backed storage layouts and GPT by default; this is a strong model for declarative Chimera storage plans. Debian's installer detects firmware requirements from kernel logs/modalias and can load redistributable firmware from installation media. FreeBSD's installer offers automatic ZFS/UFS and manual partitioning. [Sources](https://canonical-subiquity.readthedocs-hosted.com/en/latest/reference/autoinstall-reference.html), [Debian firmware](https://www.debian.org/releases/bookworm/amd64/ch02s02.en.html), [FreeBSD installer](https://docs.freebsd.org/en/books/handbook/bsdinstall/).

## 2. Supported installation profiles

| Profile | Purpose | Aurora | Network services | Storage services |
|---|---|---:|---:|---:|
| minimal | recovery/headless | off | optional | optional |
| interactive | normal desktop/server selection | optional | optional | optional |
| workstation | Aurora desktop | on | on | optional |
| server | headless/service node | off | on | on |
| developer | workstation + toolchain | on | on | on |

## 3. Step-by-step installation

### Step 0 — Firmware and boot validation

- Detect UEFI/legacy firmware mode.
- Prefer UEFI and GPT.
- Validate ACPI tables, SMBIOS/DMI data, CPU topology, memory map and TPM availability.
- Create/validate an EFI System Partition (ESP).
- Never erase a boot disk before displaying the proposed partition map.

UEFI 2.11 is the current UEFI specification and ACPI 6.6 is the current ACPI specification listed by the UEFI Forum. UEFI defines the standard environment for platform boot and OS loaders. [UEFI specifications](https://uefi.org/specifications).

### Step 1 — Hardware inventory

Collect, without changing hardware state:

- PCI/PCIe vendor/device/subsystem IDs.
- USB VID/PID/class information.
- CPU/NUMA/cache topology.
- GPU/display outputs and DRM/KMS capabilities.
- NICs, Wi-Fi, Bluetooth and virtual interfaces.
- SATA/AHCI, SAS/HBA, NVMe and virtio storage.
- RAID controllers and existing arrays.
- disks, partitions, filesystem signatures and SMART/health metadata where available.

Linux PCI drivers are matched to discovered PCI devices through the kernel PCI subsystem; driver initialization includes resource, DMA and IRQ setup. [Linux PCI driver guide](https://docs.kernel.org/PCI/pci.html).

### Step 2 — Driver and firmware resolution

**Linux sources**

- Mainline kernel driver/device IDs.
- LKDDb for a searchable mapping of hardware IDs to kernel configuration, driver and kernel versions.
- Linux-firmware for redistributable firmware, subject to each firmware license.
- Distribution package metadata as a second-stage source.

**Windows sources**

- Microsoft Update Catalog.
- Windows Driver Kit (WDK).
- Windows Hardware Lab Kit (HLK) compatibility results.
- Vendor packages only after signature and hardware-ID verification.

Linux intentionally has no stable in-kernel binary driver ABI; the preferred compatibility strategy is to upstream drivers or build against the target kernel. Linux userspace ABI is the stable compatibility boundary. [Kernel interface guidance](https://www.kernel.org/doc/html/next/process/stable-api-nonsense.html). Windows provides signed-driver mechanisms and HLK testing for Windows client/server compatibility. [Driver signing](https://learn.microsoft.com/en-us/windows-hardware/drivers/dashboard/driver-signing-offerings), [HLK](https://learn.microsoft.com/en-us/windows-hardware/test/hlk/).

### Step 3 — Network setup

- Prefer predictable device identity based on firmware/topology/MAC rather than probe order.
- Configure Ethernet/Wi-Fi profiles.
- DHCP first-run fallback; static configuration supported.
- IPv4/IPv6 dual stack.
- DNS and time synchronization.
- Optional NetworkManager/systemd-networkd compatibility adapter.
- Optional OpenSSH, SMB/Samba and NFS services.

systemd's predictable interface naming model is based on firmware, PCI topology, physical location and MAC policies and is designed to avoid probe-order instability. [systemd predictable names](https://github.com/systemd/systemd/blob/main/docs/PREDICTABLE_INTERFACE_NAMES.md).

### Step 4 — Graphics and Aurora

Chimera's graphics stack is:

`GPU driver → DRM/KMS → Mesa/Vulkan/OpenGL → Aurora compositor → Wayland clients`

Fallback chain:

`Vulkan → OpenGL/EGL → software renderer`

Weston demonstrates the same general compositor model with DRM, Wayland, X11, RDP and headless backends plus OpenGL ES, Vulkan and Pixman renderers. Chimera's Aurora compositor should provide equivalent compatibility without requiring Weston itself. [Weston backends/renderers](https://wayland.pages.freedesktop.org/weston/toc/running-weston.html).

Aurora UI goals:

- Linux-like discoverability and keyboard navigation.
- Windows-like taskbar/window management familiarity.
- Server mode with no compositor.
- Multi-monitor and HiDPI support.
- Portal-based sandbox integration.
- PipeWire optional media/audio graph.
- RDP-compatible remote desktop adapter.

### Step 5 — Disk selection and partitioning

Default proposal for a single UEFI disk:

- ESP: 512 MiB–1 GiB FAT32.
- Chimera system: remaining capacity, encrypted optionally.
- Optional swap: file or encrypted volume depending on profile.
- Optional data pool: separate disk/VG/ZFS pool.

Partition table: GPT. MBR is retained for **read compatibility and migration**, not as the preferred new installation format.

### Step 6 — RAID and dynamic storage

Provide a declarative storage model rather than hard-coding one volume manager:

- Hardware RAID/HBA passthrough.
- Linux mdraid.
- LVM2 volume groups and logical volumes.
- ZFS pools/datasets when the optional module is installed.
- Windows Storage Spaces interoperability.
- NVMe namespaces and multipath where supported.

SPDK provides an optional high-performance userspace storage path with NVMe, virtio, Ceph RBD, GPT and logical-volume support. It should be an optional accelerator, not a mandatory kernel replacement. [SPDK](https://spdk.io/doc/).

OpenZFS RAIDZ provides single, double and triple parity groups and explicitly addresses RAID-5 write-hole behavior. [OpenZFS RAIDZ](https://openzfs.github.io/openzfs-docs/Basic%20Concepts/RAID/RAIDZ.html).

### Step 7 — Filesystem selection

Default: `ext4` for maximum Linux interoperability.

Optional:

- XFS for large/server workloads.
- Btrfs for snapshots/subvolumes.
- ZFS for integrated pool/filesystem/snapshot administration.
- FAT32 for ESP.
- exFAT/NTFS interoperability modules for removable/exchange storage.
- ReFS interoperability should be treated as a Windows-storage integration target, not assumed to be a native Chimera root filesystem.

Windows Server 2025 documents NTFS and ReFS as supported filesystems and recommends ReFS for Storage Spaces Direct workloads; ReFS is not bootable and lacks some NTFS features, so Chimera should not blindly select it for the system volume. [ReFS](https://learn.microsoft.com/en-us/windows-server/storage/refs/refs-overview).

### Step 8 — Chimera directory layout

See `docs/CHIMERA_II_FILESYSTEM_LAYOUT.md`.

### Step 9 — Base system and bootloader

- Install immutable or transactional system image under `/system`.
- Generate `/etc` host configuration.
- Create service database.
- Install EFI loader entry.
- Build initramfs/early hardware registry.
- Validate kernel, modules, firmware and root filesystem before reboot.

### Step 10 — Optional services

Optional server/workstation packages include:

- OpenSSH.
- Samba/SMB.
- NFS.
- HTTP/HTTPS reverse proxy.
- DNS/DHCP.
- NTP/chrony.
- container runtime (Podman-compatible first).
- observability: journaling, metrics, tracing and OpenTelemetry-compatible exporters.
- storage: mdraid/LVM/ZFS/SPDK adapters.
- remote desktop: RDP-compatible service.

## 4. Windows compatibility model

Windows driver packages must remain Windows drivers. Chimera does **not** load arbitrary `.sys` binaries into its kernel. Instead, compatibility occurs through:

1. shared hardware identification;
2. firmware reuse where legally redistributable;
3. native Chimera drivers;
4. virtualization/IOMMU device assignment;
5. protocol adapters for SMB/NFS/RDP/USB/network/storage;
6. a controlled Windows VM/compatibility environment for devices that cannot be natively supported.

Microsoft's current WDK documentation says the latest WDK can target Windows 10, Windows Server 2016 and later, while HLK provides hardware/driver testing across supported Windows releases. [WDK](https://learn.microsoft.com/en-us/windows-hardware/drivers/download-the-wdk), [HLK](https://learn.microsoft.com/en-us/windows-hardware/test/hlk/).

## 5. Safety rules

- Never auto-wipe a disk.
- Never auto-format an existing filesystem.
- Never install an unsigned Windows driver.
- Never copy proprietary firmware without verifying redistribution rights.
- Never infer a driver's compatibility merely from a product name; match hardware IDs and kernel/OS ABI requirements.
- Never scan arbitrary Internet nodes automatically.
- Node discovery is opt-in and allowlisted.

## 6. Implementation status

The repository currently contains the safe planning layer:

- `tools/installer/installer_capabilities.json`
- `tools/installer/installer_plan.py`
- `tools/installer/chimera-installer.sh`
- `tools/installer/ChimeraInstaller.ps1`
- `tests/installer/test_installer_plan.py`

The privileged storage/driver adapters remain deliberately separated so the installer can be tested without risking the developer's disks or firmware.
