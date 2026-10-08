# Chimera II storage stack: filesystems, dynamic drives, software RAID and compression

Status: architecture and capability contract. The existing Aurora browser UI and QEMU launcher do not make the kernel able to mount every filesystem. This document does not claim broad filesystem read/write or RAID recovery is already implemented.

## Architecture

Block-device discovery → device identity/hotplug monitor → partition parser (GPT, MBR) → volume manager → optional software RAID → optional integrity/encryption layer → filesystem driver → VFS → file associations/previews. Each layer reports read, write, create, rename, delete, fsync, sparse-file, symlink, ACL, xattr, case-sensitivity and recovery capabilities independently.

## Filesystem capability matrix

| Format | Intended mode | Acceptance condition |
|---|---|---|
| ChimeraFS | native read/write | format/mount/unmount, crash recovery, metadata checksums, journaling/COW policy and fsck tests |
| FAT12/16/32 | read/write | interoperability tests with reference implementations |
| exFAT | read/write | licensed implementation and large-file/bitmap tests |
| NTFS | verified driver/helper; otherwise read-only | dirty-volume, ACL, journal and hibernation safeguards |
| ext2/3/4 | verified driver/helper | journal replay and feature-flag validation; unsupported features force read-only |
| XFS, Btrfs, ZFS | delegated/driver-dependent | version/feature and recovery tests; detection alone never implies write support |
| ISO 9660 / UDF | read-only by default for optical images | multi-session and UDF version tests |
| APFS, HFS+ | driver/helper-dependent | unsupported or encrypted volumes are read-only/unavailable, never guessed |
| NFS, SMB/CIFS, SSHFS | network filesystem adapters | authentication, reconnect, locking and offline-error tests |
| FUSE/userspace filesystems | helper-dependent | process isolation and mount-permission policy |

VFS must expose capability flags per mounted volume and never report a successful write when only a catalog entry exists. Unsupported features must fail closed or mount read-only with an explicit reason.

## Dynamic drives

- Use stable device IDs plus generation counters; names such as /dev/sdX are not stable identities.
- Device transitions: discovered → partition-scanned → volume-assembled → mounted → draining → unmounted. Cancel outstanding I/O before releasing references.
- Never auto-run programs from removable media. Support safe eject and busy-volume diagnostics.
- Test hotplug races, surprise removal, duplicate IDs, multipath devices and suspend/resume.

## Software RAID

- RAID0 provides striping/performance only, not redundancy.
- RAID1 mirrors writes; read selection may use health/latency. Degraded operation must be explicit.
- RAID10 mirrors stripes; define minimum member count and failure domains.
- RAID5/6 are deferred until parity write-hole protection, write-intent bitmap/journal, scrub, rebuild throttling and power-loss tests exist.
- Metadata includes UUID, level, member index, generation, chunk size, event counter and checksum. Reject stale/conflicting members rather than auto-assembling ambiguously.
- Rebuild uses bounded I/O, tracks progress and verifies checksums. One successful mirror read is not proof of recovery.
- Destructive create/reshape requires explicit confirmation and must never overwrite a member silently.

## Compression

- Compression is optional per-file or per-extent; external filesystems may not support it.
- Start with framed blocks using algorithm ID, uncompressed/compressed lengths, checksum and version; none and zlib/DEFLATE are the initial target. Add zstd only after runtime availability and interoperability tests.
- Bound decompressed output and memory use; validate lengths before allocation. Corruption returns an I/O error, never silently truncated data.
- Compression is not encryption and does not replace checksums, backups or RAID redundancy.

## Required validation

Format/mount/write/fsync/remount/read, crash-injection, power-loss simulation, malformed-metadata fuzzing, cross-implementation interoperability, hotplug stress, RAID member loss/rebuild/scrub, corrupted compressed block and low-space tests. Run destructive tests only on disposable image files in CI, never host block devices.
