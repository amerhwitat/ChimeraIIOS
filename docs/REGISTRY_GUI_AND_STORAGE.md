# Registry editor, registry service and optical media

## CHMRG01 service

The kernel parser remains read-only. User-space \`registryd\` owns mutation: it accepts one JSON request per line over a local Unix-domain socket, uses peer credentials, permits writes only to the \`chimera-admin\` group, rejects hardware/security/boot-critical keys, and uses generation compare-and-swap to reject stale editors.

Each change increments the hive generation. The daemon builds and verifies the binary hive, persists a write-ahead transaction record, then atomically replaces both the JSON source and binary hive with fsync. An interrupted transaction is replayed at daemon startup. Registry changes never override CPU CPUID/ID-register facts, ABI, privilege checks, memory safety or online-CPU state.

Install defaults as \`/etc/chimera/registry/{machine,environment,kernel}.json\`, binaries as matching \`.hive\` files, and the codec at \`/usr/lib/chimera/registry/registry_hive.py\`. The service socket is \`/run/chimera/registry.sock\`, mode 0660, group \`chimera-admin\`.

## Aurora Registry Editor

The Aurora app presents Machine, Environment and Kernel hives with typed values, search, add/edit/delete controls and generation-aware saves. It uses the host-injected \`window.chimeraRegistry\` bridge. When that privileged bridge is unavailable the editor is explicitly read-only; it does not claim to save browser-local data into the system registry. A WebKitGTK host bridge still needs to map the documented IPC calls to the Unix socket and Aegis authorization.

## ISO/DVD images

The Linux live edition helper uses udisks2 to create read-only loop devices and mount ISO-9660 images. Unmount removes the loop device only after successful unmount. The current helper validates the ISO-9660 primary volume descriptor; UDF and physical optical-device support are supplied by the host's udisks/kernel stack.

Native Koronos still needs optical block-device drivers, ISO9660/Rock Ridge/Joliet/UDF VFS implementations and mount syscalls. The Linux helper does not count as native Koronos VFS acceptance.
