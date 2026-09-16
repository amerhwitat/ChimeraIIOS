# Chimera II OS Performance, Repair, and Scaffolding Implementation Plan

**Goal:** Add a safe cross-edition performance, diagnostics, repair, and scaffolding layer.

**Architecture:** Declarative registries describe optimization and repair policies. A C++ advisor provides deterministic runtime hints. A Python doctor diagnoses failures and applies only explicit allowlisted local repairs. Third-party research remains adapter-only until reviewed.

**Tech Stack:** C++20, Python 3, JSON, CMake/CTest.

## Constraints
- Never execute downloaded or untrusted source automatically.
- Never auto-merge or mutate the network from research results.
- Repairs are explicit, local, reversible, and allowlisted.
- Performance claims are measured or labeled as guidance.
- Support Desktop, Server, Mobile, Edge/IoT, and CVEL.

## Tasks
1. Add performance, repair-policy, and edition-scaffold JSON registries with provenance.
2. Add native `chimera::performance` advisor and tests.
3. Add `tools/repair/chimera_repair.py` with dry-run default and explicit `--apply` for configure/build/test/cache-clean actions only.
4. Add `tools/scaffold/chimera_scaffold.py` with non-destructive cross-edition skeleton generation and tests.
5. Integrate sources, tests, tools, and registries into CMake/CTest.
6. Document IREE tuning/host targeting, OpenSSF Scorecard/SBOM practices, and safe repair boundaries; verify locally and through GitHub status.
