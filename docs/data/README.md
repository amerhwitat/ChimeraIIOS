# Chimera II OS Data Platform

Chimera exposes a common discovery and package boundary for open-source data systems.

## SQL
- SQLite: embedded/local SQL.
- PostgreSQL: open-source object-relational server; the project publishes packages for Linux, macOS and Windows.
- MariaDB: open-source relational server.
- DuckDB: embedded analytical SQL.

## NoSQL and metadata
- Apache Cassandra: distributed wide-column NoSQL.
- Apache Egeria: metadata/governance and master-data integration.
- Apache Atlas: Hadoop-oriented metadata governance when deployed.

## Apache Hadoop ecosystem
The registry covers HDFS, YARN, Hive, HBase, Spark, Tez, Kafka, Ozone and Iceberg. Chimera detects local clients and can be configured with remote cluster endpoints. Version compatibility remains an ecosystem-level concern, so Chimera records provider metadata rather than forcing one distribution.

## OpenStack
The registry covers Keystone, Nova, Neutron, Glance, Cinder, Swift, Ironic, Manila and Heat. Chimera uses the OpenStack client/API boundary and does not store credentials in repository configuration.

## Editions
Desktop and Server can host database/data services. Mobile and Edge editions favor SQLite/DuckDB or remote clients. CVEL/virtual editions can expose the same provider interfaces to remote clusters.

## Package management
`chimera-pkg data` reports known data packages. `chimera-data` reports installed client availability. Installation remains provider-specific and explicit; store or distribution restrictions are not bypassed.
