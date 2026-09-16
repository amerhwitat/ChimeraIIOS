# Database Big-Data Cloud Integration Implementation Plan

**Goal:** Add provider-neutral SQL, NoSQL, MDM/metadata, Apache Hadoop and OpenStack integration without placing third-party servers in the kernel.

**Architecture:** Versioned JSON capability registries feed a C++ data-provider interface and Python `chimera-data` CLI. Package management gains data-platform adapters while native OS/store authorities remain responsible for platform-specific installation.

**Spec:** `docs/superpowers/specs/2026-09-16-database-bigdata-cloud-design.md`

## Tasks
1. Registry: SQL/NoSQL/MDM, Hadoop and OpenStack capability/license registries.
2. C++ runtime: provider interface, availability detection and filtering with tests.
3. CLI: `chimera-data list|info|providers|doctor` with JSON output.
4. Package adapters: Linux discovery, Windows WinGet and macOS Homebrew when available; external App Store representation where no universal installer exists.
5. Hadoop: HDFS/YARN/Hive/HBase/Spark/Tez profiles and diagnostics; optional Kafka/Ozone/Iceberg.
6. OpenStack: Keystone/Nova/Neutron/Glance/Cinder/Swift/Ironic/Manila/Heat profile and read-only diagnostics.
7. CMake/editions: install registries, headers, tools and tests.
8. Docs/licenses: explain upstream roles, licenses and update policy.
9. Verification: Python compile, JSON parse, CMake build, CTest, CLI smoke tests and GitHub status checks.

## Constraints
- User-space or embedded databases only.
- Official APIs/SDKs and package providers; no wholesale upstream source copies.
- Discovery is read-only by default.
- Remote installation requires verification and explicit operator confirmation.
- Mobile/Edge default to client/embedded modes.
