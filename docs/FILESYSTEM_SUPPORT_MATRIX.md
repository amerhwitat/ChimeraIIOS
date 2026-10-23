# Filesystem Support Matrix and Universal-Mount Release Gate

Status date: 2026-10-23  
Applies to: ChimeraIIOS Koronos and the vendored kernel in OctavianOS.

## What is implemented in the current candidate

| Layer / filesystem | Current source status | What this does NOT prove |
|---|---|---|
| VFS | Mount table, longest-prefix path routing, process-scoped descriptors, open/read/write/seek/close, mount pins, mutation callback ABI; host regression test passes in canonical Koronos CI | No complete permission/credential model, persistent block layer, or universal driver support |
| tmpfs | Bounded mutable in-memory backend with copy-then-commit writes/truncates; host regression test passes in canonical Koronos CI | RAM-only; not persistent; no cold-reboot durability |
| CPIO/newc initramfs | Bounded archive validation/ingestion and staged RAMFS extraction; host tests and canonical Koronos build pass | Production target-process rootfs syscalls and readiness are not yet accepted |
| Block device | Bounded byte-offset read/write contract with capacity, logical block size, read-only flags, presence and optional flush callbacks; host test passes | PCI/virtio/ATA/NVMe discovery, DMA, interrupt handling, lifecycle and persistent storage integration are not complete |
| ISO9660 | Read-only primary-volume-descriptor (PVD) VFS candidate; synthetic-image mount, lookup, read, malformed dual-endian rejection and bounds tests pass in canonical Koronos CI | No real ISO image-backed integration test or production boot mount; Rock Ridge/Joliet, multi-extent files, writes and filesystem permissions are not implemented |
| Rock Ridge / Joliet | Not implemented | Booting an ISO image is not the same as mounting these extensions inside the OS |
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

The current branch now includes a bounded byte-offset block-device contract and a read-only ISO9660 PVD backend wired to the VFS callback ABI. The candidate intentionally supports only the primary volume descriptor and common case-insensitive ISO names with optional `;version` suffix removal. Rock Ridge, Joliet name decoding, UDF, multi-extent files, writes, and filesystem-specific permissions are not implemented. A synthetic image regression test is wired into the canonical Koronos build and passed in GitHub Actions (including rejection of a corrupted dual-endian volume descriptor). The block-device/ISO test, VFS test, tmpfs test, gzip tests, and canonical Koronos ELF build passed on completed CI commit `64d18d269cad37af4de6d8552b8c999635ac8b76`. This is host/synthetic-image verification only; the driver is not real-image-integration-tested or production-accepted.

The block adapter checks ABI, device presence, offset/length bounds, read-only writes, and unsupported flush behavior. Device lifetime remains the caller's responsibility: a mounted ISO backend must be unmounted before its device context is removed. Further review must validate descriptor sequencing, corrupt directory records, sector-boundary cases, media removal during reads, and mount/unmount races before production use.

## Release gate

A filesystem is not "implemented" merely because it has a name in a registry, a parser, a VFS callback table, or a unit test. Track each driver as **NOT IMPLEMENTED**, **IN PROGRESS**, **SOURCE ONLY**, **UNIT TESTED**, **IMAGE-INTEGRATION TESTED**, or **PRODUCTION ACCEPTED** with artifact hashes and traces. Do not advertise universal mounting until each advertised format has its own passing evidence.

The generic VFS and tmpfs have passing host regression tests, and the canonical Koronos build produced an ELF64 kernel in CI. The production ISO boot and real block-device mount path remain unverified. Installer disk-backed persistence, target-specific production userspace readiness, Aurora handoff, recovery repair, and AP-backed SMP remain separate release blockers. Keep the release gate fail-closed.
