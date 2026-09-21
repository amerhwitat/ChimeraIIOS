# Chimera II OS Open-Source Research Scan — 2026-09-21

## Scope and guardrails

This scan is a curated discovery pass for free/open-source databases, AI runtimes, parallel-processing systems, operating-system technologies, compilers, storage, networking, IoT, observability, security, virtualization, and desktop tooling that may benefit Chimera II OS. It is **not** an approval to execute, install, merge, or trust any upstream source. Every candidate remains subject to source review, license review, provenance capture, reproducible build, sandboxed testing, and explicit maintainer approval.

The full machine-readable record is in [`research/open-source-candidates-2026-09.json`](./open-source-candidates-2026-09.json).

## Highest-value safe adapter opportunities

| Priority | Candidate | Why it fits | Editions | Safe first adapter |
|---|---|---|---|---|
| A | SQLite | Small embedded state store for Hive/Nucleus, installer journals, mobile/edge metadata | Desktop, Mobile, Edge/IoT, CVEL | User-space library or reviewed system package |
| A | DuckDB | Local analytics for ISA catalogs, research data, and Nucleus workloads | Desktop, Server, CVEL | Optional CLI/library plugin |
| A | LLVM/Clang/MLIR | Toolchain, IR, assembler/backend research for Koronos and Chimera ISA work | Desktop, Server, CVEL | Separate toolchain package |
| A | OpenTelemetry | Cross-edition metrics/traces/logs boundary for Kore, Aurora, Nucleus | All editions | Stable exporter/collector ABI |
| A | Prometheus | Scrape-compatible metrics endpoint for Server/Edge/CVEL | Server, Edge/IoT, CVEL | Optional service |
| A | libsodium | High-level crypto for Aegis, signed manifests, node identity | All editions | Narrow wrapper with secure defaults |
| A | Syft + Grype | Artifact SBOM and vulnerability gates without running candidate code | All editions | CI-only audit stage |
| A | Mosquitto | Lightweight MQTT bridge for Spotnik and telemetry | Server, Mobile, Edge/IoT, CVEL | Optional broker/client with TLS and ACLs |
| A | Wasmtime | Capability-limited plugin sandbox for portable extensions | Desktop, Mobile, Edge/IoT, CVEL | Deny ambient filesystem/network by default |
| A | Zephyr | Source-level SDK and emulator target for Edge/IoT firmware | Edge/IoT, CVEL | Cross-compiler + test harness; never auto-flash |

## License and maturity comparison

- **Most integration-friendly licenses:** MIT, BSD-3-Clause, ISC, Apache-2.0, PostgreSQL License, and public-domain SQLite. These are generally easiest to adapter-wrap, but still require NOTICE/attribution and third-party dependency review.
- **Boundary-sensitive licenses:** GPL-2.0 (FRRouting, seL4 kernel), CDDL (OpenZFS), EPL/EDL (Mosquitto), AGPL-family projects, and component-specific multi-license projects such as Ceph/DPDK. These should remain external services, optional packages, or isolated research targets until compatibility is documented.
- **Maturity guidance:** established projects are reasonable candidates for protocol-level integration; production projects can be staged after reproducible-build and security review; emerging projects should be optional Aurora/CVEL tools; experimental projects must stay outside boot, installer, and security-critical paths.

Examples of current public project signals used in this scan include DuckDB’s August 26, 2026 announcement that its projects remain MIT-licensed and open source, LLVM’s current release/status page, Eclipse Mosquitto’s EPL/EDL licensing and low-power-to-server positioning, seL4’s GPL-2.0 kernel boundary explanation, and the current open-observability adoption evidence around Prometheus/OpenTelemetry. citeturn689687search2turn689687search4turn689687search6turn689687search15turn689687search3

## Edition-safe adapter map

### Desktop

- Aurora application/plugin layer: Tabularis-style database UI, DuckDB/SQLite, local ONNX/llama.cpp, OpenTelemetry local collector.
- Keep drivers, routing daemons, kernel modules, and privileged eBPF disabled by default.

### Server

- Nucleus connectors: PostgreSQL, DuckDB, Prometheus, OpenTelemetry, Mosquitto.
- Optional integration points: Ceph/S3/RBD, FRRouting, Cilium, Firecracker.
- Require explicit configuration review for routes, interfaces, storage pools, VM networking, and secrets.

### Mobile

- Prefer SQLite, libsodium, Wasmtime, MQTT client mode, and quantized offline inference.
- Do not bundle cluster managers or privileged routing/storage components.

### Edge/IoT

- Zephyr SDK/test harness, Mosquitto, SQLite, libsodium, OpenTelemetry exporters, Wasmtime where resources permit.
- Device flashing, firmware replacement, and driver installation remain manual and approval-gated.

### CVEL

- Primary research targets: LLVM/MLIR, Cranelift/Wasmtime, ONNX Runtime, Firecracker, seL4, Ray/Spark, Ceph/OpenZFS, DPDK/Cilium.
- CVEL is the preferred place for experimental adapters, synthetic datasets, fuzzing, and benchmark harnesses.

## Review and provenance workflow

1. Record repository URL, exact release/commit, license files, and transitive dependency inventory.
2. Download only through a controlled review process; calculate SHA-256 and preserve source archives.
3. Run license scanners and SBOM generation; fail closed on unknown or incompatible licenses.
4. Build in isolated CI with network restrictions and no host device access.
5. Run static analysis, unit tests, fuzz targets where available, and ABI/API compatibility checks.
6. Produce a Chimera adapter manifest describing capabilities, privileges, filesystem/network access, and rollback behavior.
7. Integrate first as an optional user-space adapter or CVEL experiment. Promote to base images only after explicit review.

## What changed in this repository

- Added `research/open-source-candidates-2026-09.json` with 25 curated candidates, license/maturity fields, edition mapping, risk, upstream links, and recommended/deferred waves.
- Added this report with comparison criteria and safe adapter opportunities.
- No upstream source was executed, installed, merged, or trusted as part of this scan.

## Sources

- DuckDB licensing/governance update: https://duckdb.org/2026/08/26/ducklabs-to-join-aws
- LLVM: https://llvm.org/
- Eclipse Mosquitto: https://mosquitto.org/
- seL4 licensing: https://www.sel4.systems/Legal/license.html
- OpenTelemetry/Prometheus adoption evidence: https://grafana.com/press/2026/03/18/grafana-labs-4th-annual-observability-survey-reveals-a-field-at-a-crossroads-ai-economics-complexity-and-the-enduring-power-of-open-source/
- Existing Chimera platform policy: [`repositories/platform-manifest.json`](../repositories/platform-manifest.json)
