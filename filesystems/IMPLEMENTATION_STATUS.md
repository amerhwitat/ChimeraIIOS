# Filesystem implementation status

This document separates a filesystem name in the catalogue from an implemented,
tested runtime driver. A catalogue entry is not a capability claim.

## Current verified scope

- QFS: a host-side image formatter and superblock inspector exist.
- QFS kernel mount, directory/inode operations, extents, allocation, journaling,
  crash recovery, snapshots, and fsck are not implemented or runtime-qualified.
- A bounded CPIO `newc` archive parser and a transactional, read-only VFS tree/lookup API now exist and are linked into the x86-64 Koronos image. The host contract test covers archive bounds, CRC, traversal, duplicate paths, missing parents and publish-on-success behavior. This is an initramfs archive index mounted from the selected raw Multiboot2 CPIO module during Koronos bootstrap. It is not a general file-descriptor VFS, writable filesystem or block-device backend; the current live/installer/recovery ring-3 payloads do not yet open or execute files from this tree.
- No native kernel filesystem driver was found for FAT12/16/32, exFAT, NTFS/NTFS3, ext2/3/4, XFS, Btrfs, ZFS, or the other catalogue entries.
- Therefore the registry marks native probe/read/write/install/live-root
  capabilities false. The filesystem matrix uses `CatalogOnly` until a
  backend has implementation and test evidence.

## Required implementation sequence

1. Extend the mounted read-only CPIO VFS with open/read/close, directory iteration, mount namespaces, permissions, reference counts and stable error semantics; connect the ring-3 process loader and init services to the published tree.
2. Implement block-device discovery, sector geometry, bounded I/O, cache,
   flush/barrier semantics, and fault injection.
3. Complete QFS as the first native filesystem: checksummed superblock,
   allocation groups/bitmaps, inode table, directories, extents, journal,
   replay, fsck, quotas, and crash-consistency tests.
4. Add FAT12/16/32 and exFAT with read/write safety, VFAT long names, and
   power-loss tests; add ISO-9660/Rock Ridge/Joliet and UDF read-only support.
5. Add ext2/3/4, XFS, NTFS3, Btrfs, and other formats one at a time, with
   independent conformance suites and explicit read/write feature flags.
6. Keep ZFS, network, userspace/FUSE, and compatibility handlers separately
   qualified; do not advertise them as native kernel drivers.
7. Gate installer selection on a runtime backend probe, format tool presence,
   and a successful temporary mount/read/write/sync/unmount test.
8. Run corruption, fuzzing, power-cut, and cross-architecture tests before
   promoting any filesystem profile from `CatalogOnly`.

## Release rule

Do not label a filesystem supported merely because it appears in
`filesystem_matrix.hpp`, `filesystem-registry.json`, or an installer profile.
Only promote an individual capability after implementation and automated
runtime evidence exist for that exact filesystem and architecture.
