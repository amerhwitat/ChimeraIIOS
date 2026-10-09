# Database Subsystem and Open-Source Backend Strategy

Chimera II OS now defines a database service boundary for relational, embedded, analytical, key-value, document and wide-column workloads. Nucleus remains the OS-level HTAP abstraction; external engines are selected behind adapters.

Recommended baseline:

- SQLite for boot metadata, local configuration and recovery state.
- DuckDB for local analytics, Parquet/JSON processing and research workloads.
- MariaDB Community Server for conventional multi-user SQL services.
- PostgreSQL for advanced transactional, extension and research workloads.
- RocksDB/LevelDB for embedded LSM storage.
- Valkey for caching, queues, streams and distributed key/value state.
- Apache Cassandra for distributed wide-column/event workloads.
- Apache CouchDB for HTTP/JSON document workloads.

ISO-Tool should build these as optional packages rather than forcing every ISO to contain every server. Package manifests record source URL, exact version, license, checksum, compiler requirements and build outcome.

Third-party binaries are not copied into the repository. The integration layer is original Chimera code plus metadata pointing to upstream projects.

## Database catalog exposed in Aurora

The ISO stages `data/registry/databases.json` at `/usr/share/chimera/database/databases.json`; Aurora's Package Manager Center exposes it through `chimera-pkg databases`. The catalog includes SQL engines (SQLite, PostgreSQL, MariaDB, MySQL Community, Firebird and DuckDB) and NoSQL/storage engines (Valkey, Apache CouchDB, Apache Cassandra, RocksDB and LevelDB).

MongoDB Community Server and CockroachDB are marked separately as source-available offerings whose current licenses are not OSI-approved open-source licenses; they are not presented as open-source-only choices. The catalog lists metadata and discovery information—it does not install or start database servers automatically. Each engine remains an optional package and must be installed/configured with its upstream license and service requirements reviewed.

