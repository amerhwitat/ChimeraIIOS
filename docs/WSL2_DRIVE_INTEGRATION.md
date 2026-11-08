# WSL2 Windows-drive integration

When the build runs inside WSL2, Windows volumes are already mounted by WSL's
DrvFs automounter (normally at `/mnt/c`, `/mnt/d`, and so on). Chimera does
not mount those volumes a second time. The build preflight discovers actual
DrvFs mounts and publishes stable aliases:

- `/mnt/drive/c` and `/mnt/drive/C` -> the existing `/mnt/c` mount
- `/mnt/drive/d` and `/mnt/drive/D` -> the existing `/mnt/d` mount

Run `tools/storage/chimera-wsl-drive-map.sh` to refresh aliases after adding
or mounting another Windows drive. The helper is a no-op outside WSL2 and
does not change WSL automount settings, Windows ACLs, or drive mount options.
It preserves existing real directories under `/mnt/drive`.

This is host/build-environment integration, equivalent to WSL's existing
Windows filesystem bridge. It does **not** claim that the Koronos native
kernel has an NTFS/DrvFs driver or that a bare-metal Chimera boot can access
Windows partitions. Native NTFS support requires a separately implemented
and tested filesystem driver and partition-mount service.
