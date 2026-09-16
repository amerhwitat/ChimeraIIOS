# Chimera II OS Database, Big-Data, MDM and OpenStack Integration Design

## Goal
Provide a provider-neutral data platform layer spanning local SQL, enterprise SQL, distributed NoSQL, master-data/metadata governance, Apache Hadoop analytics, and OpenStack infrastructure.

## Scope
- SQL: SQLite, PostgreSQL, MariaDB, DuckDB.
- NoSQL: Apache Cassandra plus pluggable document/key-value adapters.
- MDM/metadata: Apache Egeria; Apache Atlas where Hadoop is deployed.
- Apache ecosystem: HDFS, YARN, Hive, HBase, Spark, Tez, Kafka, Ozone, Iceberg, Parquet, ORC through adapters.
- OpenStack: Keystone, Nova, Neutron, Cinder, Swift, Ironic, Manila, Glance and Heat via official APIs/SDKs.
- Package manager: first-class metadata for engines/connectors, versions, architectures, dependencies, signatures/checksums and licenses.

## Architecture
1. `data/registry`: versioned engine/connector capability catalog.
2. `data/runtime`: C++ provider-neutral interfaces; databases remain user-space services or embedded libraries.
3. `data/tools`: Python CLI for discovery, health checks, profiles and diagnostics.
4. `package`: native package/data-platform provider adapters.
5. `editions`: Desktop/Server can host services; Mobile/Edge default to embedded/client modes; CVEL/virtual editions expose remote providers.
6. `docs`: security, operations, licensing and integration guidance.

## Design decisions
- Do not place database servers in the kernel.
- Integrate upstream projects through supported APIs, packages and connectors; do not wholesale-vendor upstream source.
- Discovery is read-only by default. Administrative writes require explicit configuration.
- MDM here means master-data/metadata governance integration, not proprietary device management.
- OpenStack uses official service APIs and supports Keystone authentication, Nova compute, Neutron networking, Cinder block storage, Swift object storage, Ironic bare metal, Manila shared filesystems and Glance images.
- Hadoop uses HDFS/YARN/Hive/HBase/Spark/Tez clients and service discovery without assuming one cluster topology.
- Installation requires dependency resolution, signature/checksum verification where available, audit logging, privilege separation and rollback planning.

## Security
No arbitrary remote code execution from catalogs; HTTPS/TLS and repository allowlists; signature/checksum verification; least-privilege service accounts; secrets outside manifests; audited install/upgrade/migration/export/cloud actions.

## Acceptance criteria
- Versioned data-platform registry installed with Chimera.
- `chimera-data` lists engines, capabilities and local availability and supports JSON output.
- Package manager discovers data-platform packages without pretending every vendor store has a universal CLI installer.
- CMake installs data headers, tools and registries.
- Tests cover registry parsing, provider selection, capability filtering and safe command construction.
