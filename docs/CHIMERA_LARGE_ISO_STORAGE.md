# Chimera II OS — Large ISO Storage and WSL/Docker Handling

The comprehensive ISO builder treats the ISO as a large build artifact and performs a storage preflight before Docker/rootfs/ISO work.

## What is detected

The builder detects:

- WSL2 versus a native Linux host.
- Free space on the repository filesystem.
- Mounted Windows drives exposed under `/mnt/*` in WSL.
- Native Linux filesystems using `findmnt`.
- Docker's configured root from `docker info`.
- Docker storage failures such as no-space, read-only filesystem, I/O errors and SIGBUS.
- Free space required for Docker rootfs extraction.
- Free space required for final ISO mastering.

WSL2 distributions use dynamically expanding VHDs, and Microsoft documents checking free space with `df`, resizing with `wsl --manage`, and repairing a read-only VHD when necessary. citeturn0search0

Docker Desktop on Windows uses a WSL2 backend and stores its WSL engine data in its configured disk-image location. Docker documents changing the disk-image location from Docker Desktop Settings rather than manually moving the backing file. citeturn0search2turn0search7

## Large-build relocation

When an interactive build does not have enough space, the script displays candidate drives and asks:

```
Chimera needs more storage for the large ISO build.
Enter another mounted drive/path, or press Enter to abort.
Storage path:
```

Selecting `/mnt/d`, `/mnt/e`, another mounted Linux filesystem, or another suitable path relocates the entire large-build workspace to:

```
<drive>/chimera-build/
<drive>/chimera-output/
```

The build state/checkpoint also moves with the build workspace so `--resume` continues on the selected drive.

For unattended operation, use:

```bash
CHIMERA_STORAGE_AUTO=1 bash ./build-chimera-iso.sh --resume
```

or explicitly select a drive:

```bash
sudo bash ./build-chimera-iso.sh --storage /mnt/d --clean-state
```

## WSL recommendation

For heavy filesystem operations, native Linux storage is preferred over the repository's Windows-mounted path. The final ISO can still be copied to a Windows-accessible drive after mastering.

If the WSL VHD itself is full, moving the Chimera build directory does not enlarge Docker/WSL's own storage. Microsoft documents expanding a WSL VHD with `wsl --manage <distribution> --resize ...`; Docker Desktop separately provides a disk-image location and resource controls. citeturn0search0turn0search7

## Docker storage

The script deliberately does not attempt to copy or mutate Docker Desktop's backing VHDX. If Docker itself reports storage corruption, read-only storage, I/O errors or SIGBUS, the script reports that separately.

For Docker Desktop, move or expand the Docker disk image through Docker Desktop's settings. Docker documents the disk-image location under Resources/Advanced. citeturn0search7

For WSL VHD maintenance, Microsoft warns against manipulating the distro's AppData VHDX directly with ordinary Windows tools; use the documented WSL/VHD procedures instead. citeturn0search0

## Large ISO format

The builder continues to use ISO9660 Level 3 through `grub-mkrescue`, allowing the comprehensive ISO payload to exceed the classic ISO9660 Level 1/2 file-size limitations. The final output is written to the selected large-storage filesystem, with a SHA-256 checksum beside the ISO.
