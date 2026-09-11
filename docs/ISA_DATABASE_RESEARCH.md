# ISA and Database Research Sources

## ISA/toolchain architecture

- LLVM TableGen is used as the model for declarative instruction/register descriptions and generated target tables.
- RISC-V's official specification separates a base ISA from standard, reserved and custom extensions; Chimera follows the same separation principle for compatibility metadata.

## Database candidates

- MariaDB Community Server: GPLv2 open-source server.
- PostgreSQL: PostgreSQL License.
- SQLite: public-domain deliverable code/documentation.
- DuckDB: MIT-licensed analytical database.
- RocksDB: Apache-2.0/GPLv2 dual licensing.
- LevelDB: BSD-style license.
- Valkey: BSD-licensed open-source key/value store.
- Apache Cassandra: Apache-licensed distributed wide-column database.
- Apache CouchDB: Apache-licensed document database.

The implementation records these as integration targets and does not redistribute their source or binaries. Exact release licenses and dependency licenses must be revalidated by ISO-Tool before packaging.
