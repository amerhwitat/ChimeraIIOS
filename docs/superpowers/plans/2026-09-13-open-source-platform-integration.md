# Open-Source Platform Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add provenance-first Linux/Windows/Apple-adjacent service and free/open-source application compatibility to Chimera II OS.

**Architecture:** `upstream -> provenance/license registry -> secure acquisition/build boundary -> Chimera capability adapter -> common service/application ABI -> Aurora/Koronos runtime`. Upstream projects remain separately licensed; the repository does not copy proprietary binaries or silently execute downloaded artifacts.

**Tech Stack:** JSON/JSON Schema, Python tests/tools, C/C++, Rust, Java, C#, Kotlin, Swift, TypeScript/JavaScript, Dart, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-13-open-source-platform-integration-design.md`

## Global Constraints

- Preserve upstream licenses, SPDX identifiers and attribution.
- HTTPS allowlist plus checksum/signature validation where available.
- Acquisition/staging is separate from execution/installation.
- No Secure Boot/signature/security bypass.
- Common capability APIs must not pretend native OS ABIs are identical.
- Tests precede new production behavior.

## Tasks

### 1. Provenance registry
Create `opensource/sources.schema.json`, `opensource/sources.json`, `opensource/README.md` and `tests/opensource/test_sources.py`. Test first for required fields, unique IDs, SPDX/license metadata, HTTPS upstream URLs and allowed integration modes; then add records for systemd, D-Bus, NetworkManager, PipeWire, CUPS, Samba, GTK, Qt, KDE/Plasma, Windows Terminal, PowerShell, WSL, Windows App SDK, WebKit, Swift and selected free applications. Validate and commit.

### 2. Service capability model
Create `services/service_schema.json`, `services/service_registry.json`, language bindings in C/C++/Python/Rust/Java, and `tests/services/test_service_registry.py`. Test lifecycle states (`inactive`, `starting`, `active`, `stopping`, `failed`), dependency ordering and platform resolution first. Implement `ServiceDescriptor` and `ServiceRegistry::resolve(id, platform)`, then register systemd/SCM/launchd lifecycle, D-Bus, NetworkManager, PipeWire/ALSA, CUPS/IPP, udev, Samba, timers/logging, PowerShell/terminal and WSL boundaries.

### 3. Application compatibility catalog
Create `applications/application_schema.json`, `applications/catalog.json`, README, bindings for C/C++/Rust/Python/Java/C#/Kotlin/Swift/TypeScript/Dart and `tests/applications/test_catalog.py`. Test category/platform filtering and provenance completeness first. Implement non-executing `ApplicationDescriptor`/catalog filtering. Cover file manager, terminal, editor, office/document, image/PDF, media, browser/WebKit shell, archive, calculator, system monitor, disk/network/developer/accessibility/recording/backup/package-management families.

### 4. Native platform adapters
Create Linux/Windows/macOS service and application adapter boundaries plus native tests. Test capability reporting first. Implement portable adapters with explicit unsupported-operation results and mappings for lifecycle, IPC, terminal, notifications, filesystem/open-file, printing, audio/media and application-launch boundaries. Compile with C11/GCC/Clang-compatible flags and platform guards.

### 5. Language matrix and CI
Create `tools/validate_open_source_matrix.py` and `.github/workflows/open-source-integration-ci.yml`; complete bindings for Rust/Python/Java/C#/Kotlin/Swift/TypeScript/Dart and integrate existing desktop conventions. Test the matrix validator first, then add CI for Python, C/C++, Rust, Java, C#, Kotlin, Swift, Node.js/TypeScript and Dart with explicit toolchain availability handling.

### 6. Secure source automation
Create `tools/update_open_source_sources.py`, `tools/validate_provenance.py`, `build/open_source/README.md`, `build/open_source/fetch_sources.py`, and `build/open_source/build_manifest.json`. Test HTTPS-only sources, allowlist enforcement, checksum verification and non-executing staging first. Reuse the existing driver-acquisition policy patterns; manifests declare build commands and provenance but fetching never executes them.

### 7. Documentation
Create `docs/OPEN_SOURCE_INTEGRATION.md`, `docs/SERVICES_COMPATIBILITY.md`, `docs/APPLICATION_COMPATIBILITY.md`, `docs/SOURCE_PROVENANCE.md`; update `docs/DESKTOP_COMPATIBILITY.md`, affected language READMEs and root `README.md`. Test path/link references first. Document architecture, licensing, attribution, service/application families, acquisition/build workflow and language matrix; cite official upstream sources and distinguish compatibility from proprietary redistribution.

### 8. Full verification audit
Run focused Python tests, C/C++ compilation, Rust checks, Java tests and available C#/Kotlin/Swift/Node/Dart checks. Validate all registries and provenance metadata. Inspect the final tree for proprietary binaries, secrets, unsafe downloads and license omissions. Inspect GitHub Actions runs/logs. Only report completion when fresh verification evidence supports each claim.
