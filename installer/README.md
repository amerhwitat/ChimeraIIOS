# Chimera II Graphical Installer

The installer is a GUI-first application with full keyboard navigation and mouse support.

## Screens

- Welcome / firmware mode
- Language and keyboard
- Hardware summary
- Disk and partition selection
- Partition editor
- Filesystem selection
- Bootloader selection
- Installation options
- Installation progress
- Boot configuration
- Completion / reboot

## Adaptive inventory engine

`chimera_installer.py` provides an inventory-first planner used by the graphical or automation front ends. It detects firmware mode, architecture, CPU/core count, memory, storage, networking tools, virtualization, Secure Boot state when available, and evidence of existing operating systems. It produces a reviewable JSON installation plan and selects a compatible Chimera II OS edition using explicit heuristics.

Supported editions: Desktop, Server, Mobile, Edge, IoT and CVEL.

The design is intentionally adaptive rather than claiming an undefined form of “superintelligence”: hardware facts, compatibility rules, provenance and explicit user choices determine the plan.

## Partitioning

Backends must support GPT and MBR where applicable and expose safe operations for SSD, NVMe and HDD devices. Supported filesystem implementations are selected from the actual Chimera VFS capability registry; unsupported formats are never presented as writable options.

The UI clearly distinguishes:

- existing data
- ESP/boot partitions
- system partitions
- swap/pagefile-equivalent areas
- free/unallocated space
- partitions scheduled for deletion
- partitions scheduled for formatting

No destructive operation is performed until the complete plan is displayed and explicitly confirmed. The automation planner never silently erases disks or overwrites another OS.

## Firmware and hardware discovery

UEFI/ACPI are the primary firmware discovery interfaces. The UEFI Forum publishes UEFI 2.11 and ACPI 6.6 as current specification versions. The Linux kernel documentation also describes UEFI/ACPI tables and the UEFI memory map as platform information available during early boot.

## Progress

The installer reports weighted phases:

1. Prepare target
2. Partition
3. Format
4. Copy base system
5. Install bootloader
6. Configure boot menu
7. Install drivers/services
8. Verify
9. Finalize

The progress model supports cancellation only at safe checkpoints and writes an installation journal for recovery/debugging.

## Automation

Windows: `installer\\install-chimera.bat` or `installer\\install-chimera.ps1`

POSIX: `installer/install-chimera.sh`

All-edition builds: `tools/build/build_all_editions.py`, with `.bat`, `.ps1`, and `.sh` wrappers.

Cross-architecture builds require the appropriate compiler/toolchain; the build orchestrator reports failures instead of presenting a failed foreign-architecture build as successful.

## Reboot

The final page provides `Reboot`, `Return to Live`, and `Shutdown`. Before reboot, the installer validates the boot configuration and flushes storage operations.
