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


## Network and optical mount namespaces

- `/mnt/chimera/network/<share>` — administrator-mounted SMB/CIFS network shares. The supplied helper uses SMB 3.1.1 and restrictive mount flags.
- `/mnt/chimera/media/<image-or-device>` — read-only ISO-9660/UDF images and optical drives; execution and device nodes are disabled.
- `/srv/smb` — optional server-side Samba export data; never expose it as a guest-writable share by default.
- `/etc/chimera/identity` — local SSSD/realmd policy and non-secret directory-service configuration. Passwords and Kerberos tickets must remain in protected system credential stores, not this directory or the ISO.
