# Chimera II OS: Performance, Automatic Repair, and Scaffolding Research

## Research basis

Chimera now records performance guidance separately from executable integrations. IREE documents host CPU targeting and optimization levels, and its tuning workflow explicitly uses compile/benchmark/knob iteration; these are represented as guidance rather than hard-coded claims about speed. OpenSSF Scorecard provides automated supply-chain checks and recommends SBOM publication, so the repair/research layer treats provenance and dependency evidence as first-class data.

## Implemented layer

- `performance/registry/performance_profiles.json` stores cross-edition optimization guidance.
- `performance/registry/repair_policies.json` defines the allowlist for local repairs.
- `performance/registry/scaffolds.json` defines edition layouts.
- `include/chimera/performance/performance.h` and `src/performance/performance.cpp` provide dependency-free native hints.
- `tools/repair/chimera_repair.py` diagnoses build state and defaults to dry-run. `--apply` executes only explicit local CMake/CTest actions.
- `tools/scaffold/chimera_scaffold.py` creates non-destructive edition directories and a manifest.

## Automatic repair boundary

Automatic repair means deterministic remediation of known local build/test conditions. It does **not** mean downloading arbitrary patches, executing generated source, merging Git branches, changing credentials, or mutating remote infrastructure.

## Performance methodology

1. Discover hardware and workload characteristics.
2. Select a bounded configuration.
3. Build with the appropriate native target when safe.
4. Benchmark before/after changes.
5. Persist measured results with provenance.
6. Promote only reviewed, reproducible changes.

This avoids treating a generic optimization heuristic as a guaranteed performance improvement.

## Editions

The same policy vocabulary is used across Desktop, Server, Mobile, Edge/IoT, and CVEL. Platform-specific acceleration remains behind adapters so a missing GPU/NPU/runtime does not prevent a baseline build.

## External references

- IREE CPU deployment guidance: https://iree.dev/guides/deployment-configurations/cpu/
- IREE tuning: https://iree.dev/reference/tuning/
- OpenSSF Scorecard: https://openssf.org/scorecard/
- OpenTelemetry: https://opentelemetry.io/
- DuckDB: https://duckdb.org/
