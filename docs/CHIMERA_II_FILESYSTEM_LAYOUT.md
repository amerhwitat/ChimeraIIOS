# Chimera II OS Filesystem and Directory Layout

The target filesystem follows familiar Unix semantics while reserving Chimera-specific namespaces. The installer may materialize this tree on the target root filesystem.

## Ten-level reference hierarchy

```text
/
├── boot/
│   └── efi/
│       └── EFI/
│           └── CHIMERA/
│               └── loaders/
│                   └── profiles/
│                       └── hardware/
│                           └── <platform>/
│                               └── <arch>/
│                                   └── <version>/
├── system/
│   └── chimera/
│       └── kernel/
│           └── modules/
│               └── <release>/
│                   └── <arch>/
│                       └── <subsystem>/
│                           └── <driver-family>/
│                               └── <module>/
│                                   └── manifest.json
├── usr/
│   ├── bin/
│   ├── sbin/
│   ├── lib/
│   ├── include/
│   └── share/
├── etc/
│   ├── chimera/
│   │   ├── installer/
│   │   ├── hardware/
│   │   ├── drivers/
│   │   ├── network/
│   │   ├── storage/
│   │   ├── aurora/
│   │   └── services/
│   ├── fstab.d/
│   └── secureboot/
├── var/
│   ├── log/
│   ├── lib/
│   │   ├── chimera/
│   │   ├── package/
│   │   └── cognition/
│   ├── cache/
│   └── spool/
├── run/
│   ├── chimera/
│   ├── services/
│   └── devices/
├── dev/
├── proc/
├── sys/
├── home/
│   └── <user>/
├── root/
├── srv/
│   ├── ssh/
│   ├── smb/
│   ├── nfs/
│   ├── web/
│   └── chimera-node/
├── opt/
│   ├── chimera/
│   │   ├── aurora/
│   │   ├── drivers/
│   │   ├── spdk/
│   │   └── research/
├── lib/
├── lib64/
├── mnt/
├── media/
└── tmp/
```

## Namespace rules

- `/boot` — boot artifacts only.
- `/system` — immutable/transactional Chimera OS payloads.
- `/usr` — shared userland programs and libraries.
- `/etc/chimera` — machine-specific Chimera configuration.
- `/var/lib/chimera` — mutable databases, state and caches.
- `/srv/chimera-node` — optional network-node data exchange endpoint.
- `/opt/chimera` — optional components that are not part of the base image.
- `/run/chimera` — volatile runtime state.
- `/dev`, `/proc`, `/sys` — kernel/device pseudo-filesystems.

## Driver store

`/system/chimera/kernel/modules/<release>/<arch>/` contains only Chimera-compatible kernel modules. Linux `.ko` and Windows `.sys` files are not interchangeable binaries. Windows packages are retained only in an interoperability/import cache when licensing permits.

## Transactional updates

A future installer/update engine should create versioned `/system/chimera/kernel/<version>` and switch an EFI boot entry or bootloader generation atomically. Rollback keeps the previous generation intact until post-boot health checks succeed.


## Linux Filesystem Hierarchy Standard compatibility

The installed Linux live edition follows the conventional FHS layout. The Chimera-specific \`/system\` namespace is additive and must not replace standard paths.

- \`/bin -> /usr/bin\`, \`/sbin -> /usr/sbin\`, \`/lib -> /usr/lib\`, and architecture-appropriate \`/lib64 -> /usr/lib64\` are compatibility links on usr-merged images.
- \`/usr/local/{bin,sbin,lib,share}\` is reserved for administrator-installed software.
- \`/etc\` contains host configuration; \`/etc/chimera/registry\` contains the editable CHMRG01 JSON source and generated binary hives.
- \`/var/lib/chimera/registry\` is reserved for future transaction history and snapshots; the active service currently commits its journal beside the hive under \`/etc/chimera/registry\`.
- \`/var/log\`, \`/var/cache\`, \`/var/tmp\`, \`/var/spool\` and \`/var/lib\` retain standard FHS meanings.
- \`/run\` is volatile; \`/run/chimera/registry.sock\` is the local registry IPC endpoint.
- \`/media/<user>/<label>\` is the desktop automount location for removable optical media. ISO files use udisks2 read-only loop devices.
- \`/mnt/smb/<server>/<share>\` is the optional administrator-managed SMB mount convention. Desktop GVFS sessions may expose shares under \`/run/user/<uid>/gvfs\`.
- \`/mnt\` is for temporary administrator mounts; \`/srv\` is for data exported by this host, not client mountpoints.
- \`/dev\`, \`/proc\`, and \`/sys\` are runtime-managed device and kernel pseudo-filesystems and must not be populated as ordinary static directories.

## Filesystem support truth

The filesystem catalogue separates Linux live-image interoperability from Koronos native VFS support. ISO-9660, Rock Ridge, Joliet and UDF are mounted by the Linux live kernel/udisks2 path in this integration. CIFS/SMB and NFS are user-space/kernel Linux integrations. These are not evidence that Koronos has native drivers or a production VFS mount implementation. QFS remains a prototype until its format, crash consistency and mount path pass native tests.

## FHS compatibility and usr-merge

The installed root follows the Filesystem Hierarchy Standard conventions in
addition to the Chimera-specific /system namespace:

- /usr/bin and /usr/sbin contain user and administrator commands.
- /usr/lib and /usr/lib64 contain architecture-specific libraries and services.
- /usr/share contains architecture-independent registries, schemas, catalogs and desktop assets.
- /etc contains local machine configuration; /var/lib contains persistent mutable state.
- /run contains volatile runtime state; /tmp and /var/tmp are world-writable sticky directories.
- /dev, /proc and /sys are mounted pseudo-filesystems, not ordinary persistent data.
- /home and /root hold user and administrator data; /srv holds service data.
- /opt holds optional third-party payloads; /mnt and /media are mount points.

On usr-merged installations, /bin, /sbin, /lib and /lib64 are relative
compatibility symlinks into /usr. The rootfs preparation helper only creates
these links when the link and its target are absent; it never replaces an
existing directory. It accepts only an explicit staging root and refuses /.

Optical images and physical CD/DVD media are mounted on demand under /media
using ISO9660 or UDF with read-only, nosuid, nodev and noexec options. The
installer must discover filesystem UUIDs before generating /etc/fstab; the
checked-in fstab example contains placeholders and must never be installed
verbatim as a production mount table.
