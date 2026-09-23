# Chimera Knowledge Fabric

The knowledge fabric is a staged, provenance-preserving system for periodically retrieving public information, classifying it, deduplicating it, compressing it and making it available to local Chimera services.

## Pipeline

fetch -> parse -> normalize -> classify -> hash -> deduplicate -> summarize/embed -> columnar store -> index -> publish

JSON is the interchange/audit format. A columnar store is the analytics format. Apache Parquet is supported as the external interchange target because it is column-oriented and supports compression, encoding, dictionary pages and page indexes. citeturn0search2turn0search14

The system never treats downloaded material as executable code. Sources are provenance records. License metadata is retained.

## Autonomous patching

Knowledge may generate a proposed patch, but native OS changes pass through:
1. isolated build;
2. static analysis;
3. unit/integration tests;
4. reproducible build verification;
5. artifact hash;
6. signature/policy verification;
7. staged deployment;
8. health check;
9. automatic rollback on failure.

Kernel, bootloader, security, networking and privileged changes require an explicit administrator policy. There is no unrestricted self-modifying privileged execution path.

## Federation

Chimera peers exchange signed knowledge bundles using content hashes and manifests. Duplicate records are rejected by canonical hash; semantic near-duplicates are clustered without deleting the original provenance records.
