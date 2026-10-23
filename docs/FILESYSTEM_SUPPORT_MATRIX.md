# Filesystem Support Matrix and Universal-Mount Release Gate

Status date: 2026-10-23  
Applies to: ChimeraIIOS Koronos and the vendored kernel in OctavianOS.

## What is implemented in the current candidate

| Layer / filesystem | Current source status | What this does NOT prove |
|---|---|---|
| VFS | Mount table, longest-prefix path routing, process-scoped descriptors, open/read/write/seek/close, mount pins, mutation callback ABI | No complete permission/credential model, persistent block layer, or universal driver support |
| tmpfs | Bounded mutable in-memory backend with copy-then-commit writes/truncates | RAM-only; not persistent; no cold-reboot durability |
| CPIO/newc initramfs | Bounded archive validation/ingestion and staged RAMFS extraction code | Production extraction-to-VFS lifecycle and target process-visible root are not yet accepted |
| ISO9660 / Rock Ridge / Joliet | **Not implemented as a mountable block-backed VFS driver** | Booting an ISO image is not the same as mounting its filesystem inside the OS |
| UDF | Not implemented | No read/write support claimed |
| FAT12 / FAT16 / FAT32 | Not implemented | No block-backed mount, mutation, or crash-consistency claims |
| exFAT | Not implemented | No mount support claimed |
| ext2 / ext3 / ext4 | Not implemented | No journaling, metadata, or recovery support claimed |
| NTFS | Not implemented | No Windows volume mount or write support claimed |
| XFS | Not implemented | No allocation-group/log recovery support claimed |
| QFS | Unresolved name; identify the exact on-disk format before implementing | Must not treat unrelated filesystems sharing an acronym as compatible |
| Btrfs / ZFS | Not implemented | No checksums, snapshots, copy-on-write, pool/import, or recovery claims |
| F2FS / JFS / ReiserFS / HFS+ / APFS / UFS / BSD FFS / Minix | Not implemented | No mount support claimed |
| SquashFS / EROFS / cramfs / ROMFS | Not implemented | No read-only image driver claimed |
| NFS / SMB / 9P / other network or host-shared filesystems | Not implemented | No network transport/authentication/mount support claimed |
| procfs / sysfs / devtmpfs / overlayfs | Not implemented as complete VFS backends | Kernel pseudo-filesystem semantics and overlay whiteouts are absent |

## Required implementation architecture

1. **Block-device contract**: bounded sector reads/writes, device capacity and logical block size, error propagation, flush/barrier support, and removable-media lifetime. Drivers must never assume a device exists because a descriptor is catalogued.
2. **Filesystem driver ABI**: probe/mount/unmount, lookup, stat, read, write, create, truncate, mkdir, unlink, rename, sync, and filesystem-specific capability flags. A missing operation must fail explicitly, never silently succeed.
3. **Read-only image path first**: ISO9660 (including selected Rock Ridge/Joliet features), UDF, SquashFS, EROFS, cramfs and ROMFS need bounded metadata parsing, symlink/path confinement, malformed-image fuzz tests, and image-backed integration tests.
4. **Mutable disk filesystems**: FAT variants and ext2 first, followed by ext3/ext4 and NTFS/XFS/QFS only after format-specific allocation, journaling/log replay, permissions, locking, crash recovery and power-loss tests exist. QFS must be specified by vendor/format.
5. **Advanced / platform-specific filesystems**: Btrfs, ZFS, APFS and network filesystems require independent designs and substantial feature work; do not promise write support merely because a read-only parser exists.
6. **Security**: process-owned credentials, UID/GID and mode checks, mount namespace policy, symlink handling, path traversal defenses, TOCTOU-safe lookup, locking, and block-device authorization must be in place before exposing mutations to ring 3.
7. **Acceptance per driver**: known-good and malformed images, boundary/overflow tests, fuzzing, read/write/rename/unlink tests as applicable, remount tests, fault-injected I/O, sync/power-loss recovery, and a production ISO/VM test with raw evidence. Unsupported formats must return a clear unsupported-format error.

## 2026-10-23 block I/O and ISO9660 candidate

The current branch now includes a bounded byte-offset block-device contract and a read-only ISO9660 PVD backend wired to the VFS callback ABI. The candidate intentionally supports only the primary volume descriptor and common case-insensitive ISO names with optional `;version` suffix removal. Rock Ridge, Joliet name decoding, UDF, multi-extent files, writes, and filesystem-specific permissions are not implemented. A synthetic image test and build-script/CTest entries were added, but **they have not yet been compiled or executed in this environment**; therefore the driver is SOURCE ONLY, not unit-tested or production-accepted.

The block adapter checks ABI, device presence, offset/length bounds, read-only writes, and unsupported flush behavior. Device lifetime remains the caller's responsibility: a mounted ISO backend must be unmounted before its device context is removed. Further review must validate descriptor sequencing, corrupt directory records, sector-boundary cases, media removal during reads, and mount/unmount races before production use.

## Release gate

A filesystem is not "implemented" merely because it has a name in a registry, a parser, a VFS callback table, or a unit test. Track each driver as **NOT IMPLEMENTED**, **IN PROGRESS**, **SOURCE ONLY**, **UNIT TESTED**, **IMAGE-INTEGRATION TESTED**, or **PRODUCTION ACCEPTED** with artifact hashes and traces. Do not advertise universal mounting until each advertised format has its own passing evidence.

The current candidate supports the generic VFS API and tmpfs only at source level; these changes have not been verified by a fresh kernel build or production ISO boot in this closeout cycle. Installer disk-backed persistence, target-specific production userspace readiness, Aurora handoff, recovery repair, and AP-backed SMP remain separate release blockers. Keep the release gate fail-closed.
