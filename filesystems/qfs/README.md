# Chimera QFS

QFS is the native Chimera II OS block-filesystem format.

- Default allocation block: **4096 bytes / 4 KiB**
- Configurable blocks: **4, 8, 16, 32, or 64 KiB**
- Sector size is recorded separately.
- The on-disk superblock records block geometry explicitly.
- A block larger than the running kernel page size is not selected by the installer for native mounts.
- Research images may be formatted with a larger block using `--allow-unsafe-page-size`, but the native mount layer must reject incompatible geometry.

The current formatter creates a QFS image/superblock contract. Full directory, extent, journal, snapshot, and recovery implementation remains a kernel/filesystem development track; it is not represented as complete merely by the formatter.
