# Chimera II OS Database Subsystem

Koronos treats databases as userspace services behind a stable database IPC ABI. The kernel does not embed a full SQL/NoSQL engine. This preserves microkernel isolation while allowing the OS image, Nucleus HTAP layer, package manager and applications to select an appropriate backend.

## Supported open-source integration targets

| Backend | Model | License | Intended role |
|---|---|---|---|
| MariaDB Community Server | relational | GPLv2 | primary server SQL |
| PostgreSQL | relational | PostgreSQL License | advanced SQL/transactions |
| SQLite | embedded relational | public domain | system-local metadata |
| DuckDB | analytical | MIT | OLAP/data science |
| RocksDB | key-value | Apache-2.0/GPLv2 | high-performance local KV |
| LevelDB | key-value | BSD-3-Clause | compact local KV |
| Valkey | key-value/cache/streams | BSD-3-Clause | distributed cache and messaging |
| Apache Cassandra | wide-column | Apache-2.0 | distributed HTAP/event data |
| Apache CouchDB | document | Apache-2.0 | JSON/document workloads |

The repository stores **adapters and manifests, not third-party database source trees or binaries**. ISO-Tool may fetch and build an explicitly selected upstream release and record its license, checksum, source URL and build result.

SQLite is especially suitable for early boot metadata because its deliverable code/documentation is public domain. MariaDB Community Server is GPLv2; PostgreSQL uses its own permissive PostgreSQL License; DuckDB is MIT; Valkey is BSD; RocksDB offers Apache-2.0/GPLv2; and CouchDB is Apache-2.0. Verify the exact upstream release before redistribution.

## Architecture

```text
Application / Nucleus / Hive
          |
     Database ABI
          |
   Koronos IPC rings
          |
 +--------+---------+----------------+
 | MariaDB | PostgreSQL | SQLite/DuckDB |
 | RocksDB | LevelDB   | Valkey/Cass.  |
 | CouchDB | future adapters          |
 +------------------------------------+
```
