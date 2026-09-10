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

No destructive operation is performed until the complete plan is displayed and explicitly confirmed.

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

## Reboot

The final page provides `Reboot`, `Return to Live`, and `Shutdown`. Before reboot, the installer validates the boot configuration and flushes storage operations.
