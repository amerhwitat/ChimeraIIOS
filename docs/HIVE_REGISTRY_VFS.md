# Hive Registry Database and VFS

Hive is the persistent configuration database for Chimera II OS. The current userspace backend is a C++20 store with an append-only write-ahead log. POSIX hosts use flock, fsync and atomic rename; Windows uses LockFileEx, the CRT file-descriptor I/O layer, _commit and MoveFileEx replacement semantics.

## Storage and recovery

Default location for per-user Aurora settings: $XDG_DATA_HOME/chimera/hive, falling back to ~/.local/share/chimera/hive. Set CHIMERA_HIVE_DIR to select another database. The system service instance uses /var/lib/chimera/hive.

- registry.db is an atomically replaced snapshot with a monotonically increasing sequence.
- registry.wal contains set/delete records followed by commit records. Recovery applies only complete committed transactions.
- registry.lock uses advisory flock on POSIX hosts and an exclusive LockFileEx byte-range lock on Windows to serialize writers across processes.
- Checkpointing durably flushes the temporary snapshot, atomically replaces the database snapshot, then truncates and durably flushes the WAL. POSIX also fsyncs the containing directory; Windows uses MoveFileEx with replace-existing and write-through flags. A crash after snapshot publication but before WAL truncation is safe because replay skips transaction sequence numbers already represented in the snapshot.
- Database files are created with restrictive permissions; keys and values are length bounded.

The WAL supports atomic multi-key batches: all set records in a batch share one transaction ID and become visible only after the commit record is durable. The next extensions are schema migrations and stronger snapshot/WAL integrity checks. The current format is a Chimera-native settings store; it is not a Windows regf hive reader/writer and does not claim binary compatibility with Windows registry hive files.

## Commands

chm-registry list
chm-registry get settings/system.theme
chm-registry set settings/system.theme dark
chm-registry delete settings/system.theme
chm-registry compact
chm-registry check

Use --db DIR to select a test or alternate database.

## Aurora integration

Aurora Settings reads the legacy settings.conf mirror for compatibility, then overlays values from Hive under settings/<setting-key>. Changes are persisted to Hive and mirrored to the legacy file when writable.

When Qt 6 Widgets is available at build time, CMake builds aurora-registry-editor. It provides a table view, selection, save/modify, delete, and checkpoint/recovery actions. Headless builds continue to build the CLI and database without Qt.

## Registry VFS

When libfuse3-dev is available, CMake builds chm-registry-mount. It projects registry paths as files under a FUSE mount: registry key settings/system/theme appears as /settings/system/theme; reads and writes go through the transactional store. Directories are inferred from key prefixes. Mount explicitly:

sudo mkdir -p /run/chimera/registry
sudo chm-registry-mount /var/lib/chimera/hive /run/chimera/registry

An optional systemd unit is installed with the FUSE target; enable it only when the administrator wants the system registry mounted. FUSE support is optional and does not prevent a headless ISO build.

## Process integration boundary

This release wires Aurora's settings persistence to Hive, but it does not yet project values into live Koronos process environments or mutate kernel state. Such changes require a versioned Koronos IPC contract, per-key authorization, audit records, rollback policy, and validated syscall/interrupt/SMP primitives. Do not treat registry edits as live kernel configuration until that interface is implemented and tested.
