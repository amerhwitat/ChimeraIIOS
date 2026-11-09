# WSL Windows-drive aliases

Run `sudo bash tools/wsl/map-windows-drives.sh` inside WSL to create aliases such as:

- `/mnt/drive/C` → the existing WSL mount `/mnt/c`
- `/mnt/drive/D` → the existing WSL mount `/mnt/d`

The helper does **not** mount disks or change WSL automount settings. It only aliases existing mounts whose filesystem type is reported by `findmnt` as `drvfs` or `9p`. It is idempotent and refuses to replace existing files, directories, or mismatched symlinks.

Optional environment variables:

- `CHIMERA_WSL_MNT_ROOT`: source mount root (default `/mnt`)
- `CHIMERA_WINDOWS_DRIVE_ROOT`: alias root (default `/mnt/drive`)
- `CHIMERA_WSL_DRIVE_DRY_RUN=1`: print actions without creating aliases

This is a **WSL host integration**, not a native Koronos NTFS/DrvFs filesystem driver. Native Koronos support still requires a VFS/block-device path, partition discovery, NTFS metadata and journaling support, permissions/ACL translation, Unicode/case behavior, and crash-safe write tests.
