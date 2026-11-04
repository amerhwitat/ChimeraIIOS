# Registry editor, registry service and optical media

## CHMRG01 service

The Koronos kernel parser remains read-only. User-space registryd owns mutation over /run/chimera/registry.sock, a local Unix-domain socket. It checks peer credentials, permits writes only to the chimera-admin group, rejects hardware/security/boot-critical keys and uses generation compare-and-swap to reject stale editors.

Each change increments the hive generation. The daemon builds and verifies the binary hive, persists a write-ahead transaction record, then atomically replaces the JSON source and binary hive with fsync. An interrupted transaction is replayed at daemon startup. A process-wide lock serializes writers. Registry changes never override CPU CPUID/ID-register facts, ABI, privilege checks, memory safety or online-CPU state.

The Linux live-image builder installs the three defaults in /etc/chimera/registry, builds matching .hive files and enables chimera-registryd.service. The chimera-admin group is populated from existing sudo group members before the desktop starts. Installed-system account provisioning must apply the same policy.

## Aurora Registry Editor

The Aurora app presents Machine, Environment and Kernel hives with typed values, search, add/edit/delete controls and generation-aware saves. The WebKitGTK kiosk injects window.chimeraRegistry only into the exact packaged local Aurora entrypoint; calls are forwarded to the local Unix socket. If the bridge or admin authorization is unavailable, the editor is explicitly read-only or displays the service error. It never claims browser-local storage is the system registry.

Hardware identity, CPU feature selection, memory limits, SMP-online state, security and boot-critical keys are protected from ordinary registry edits. The kernel still validates binary hives independently.

## SMB and directory services

The Windows Network app uses the trusted local WebKit bridge for local-link discovery, explicit SMB host share listing, realm status, domain join and LDAP search. Domain join requires a pre-existing Kerberos ticket and administrator authorization. Passwords are never persisted in the registry.

## ISO/DVD images

The Optical Media app selects ISO images through a native file chooser or mounts a physical /dev/srN drive. The Linux helper validates ISO-9660 or UDF volume recognition, creates a read-only loop device for image files, and mounts through udisks2 with read-only options. Unmount removes a loop device only after successful unmount.

Native Koronos still needs optical block-device drivers, ISO9660/Rock Ridge/Joliet/UDF VFS implementations and mount syscalls. The Linux helper does not count as native Koronos VFS acceptance.
