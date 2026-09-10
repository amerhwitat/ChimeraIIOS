# Chimera II OS — CI/CD Plan for a Public Research Operating System

## Objectives

The CI/CD system must make the project reproducible, auditable, multi-target and safe to publish as research software.

## Pipeline

```text
Commit / PR
   |
   +--> License + provenance audit
   |
   +--> Format / lint / static analysis
   |
   +--> C / C++ / Assembly build matrix
   |       x86-64 | ARM64 | Cortex-M | R8192 simulator | C8192 simulator
   |
   +--> Unit tests
   |
   +--> ISA conformance / ABI tests
   |
   +--> Package tests (.deb / rpm / pacman metadata / universal fabric)
   |
   +--> QEMU boot + kernel smoke tests
   |
   +--> Aurora Web UI browser tests
   |
   +--> Mobile target configuration tests
   |
   +--> Documentation + link + sitemap validation
   |
   +--> SBOM + dependency/license scan
   |
   +--> Signed artifact generation
   |
   +--> Release / mirror publication
```

## Required gates

### 1. Source integrity

- Reject committed credentials and private keys.
- Check SPDX/license metadata.
- Record third-party provenance.
- Prevent accidental vendoring of incompatible or proprietary source.

### 2. Build matrix

At minimum:

- GCC and Clang on Linux.
- x86-64 host.
- ARM64 cross build.
- Cortex-M cross build where the toolchain is available.
- Chimera N-bit emulator/runtime.
- CISC/RISC ISA tooling.
- Web UI static build and browser checks.

### 3. Functional tests

- RegisterN arithmetic and serialization.
- ISA encode/decode round trips.
- Boot ABI structures.
- Kernel service contracts.
- Spotnik networking adapters.
- VFS/package-fabric transactions.
- Mobile target policies.
- Aurora desktop/window contracts.
- Web terminal sandbox boundaries.

### 4. QEMU and integration testing

Use QEMU for deterministic pre-hardware validation. The research corpus explicitly recommends emulator → assembler/linker → host microkernel → x86/UEFI → ARM/embedded ports before FPGA feasibility. fileciteturn66file7L503-L519

### 5. Documentation gate

Every release should validate:

- README links;
- documentation links;
- repository links;
- sitemap syntax;
- `robots.txt` syntax;
- no accidental `noindex` on public research pages;
- bibliography entries;
- source/provenance references.

### 6. Security and release gate

Release artifacts should include:

- SHA-256 checksums;
- SBOM;
- license/provenance report;
- build metadata;
- signed tags/releases when signing infrastructure is available;
- reproducible-build notes;
- rollback instructions.

The mobile/robotics research architecture already specifies secure boot, signed artifacts, measured update state, memory permissions, capability-like IPC, encrypted management channels and watchdogs as security goals. fileciteturn66file5L394-L407

## Release channels

1. **Nightly research** — every successful main-branch build.
2. **Experimental** — feature-complete research milestones.
3. **Release candidate** — all mandatory gates pass.
4. **Stable research release** — tagged, checksummed and archived.
5. **Mirror release** — the same Git tag is propagated to GitLab, Codeberg/Forgejo and SourceHut when mirrors are configured.

## CI/CD federation

GitHub Actions remains the primary CI for the canonical repository. Secondary forges should consume the same Git tag and run their native CI where possible. Codeberg provides Forgejo Actions/Pages, while SourceHut provides builds.sr.ht and repository/project infrastructure. citeturn1search16turn1search0

## Branch policy

- `main`: integration branch.
- `feature/*`: isolated development.
- `release/*`: release preparation.
- tags: immutable research releases.

No release is declared stable merely because a build starts. A release requires completed build, test, documentation, security and artifact verification.

## Future hardware CI

When physical Chimera hardware exists, add self-hosted runners for:

- R8192 FPGA prototype;
- C8192 FPGA prototype;
- ARM development boards;
- x86 reference machines;
- mobile SoC boards.

Hardware jobs remain downstream validation; QEMU/emulator jobs stay mandatory for deterministic pull-request coverage.
