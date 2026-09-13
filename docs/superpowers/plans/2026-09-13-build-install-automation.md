# Cross-Platform Build and Installer Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Chimera II OS reproducibly configure, build, test, package, install, and publish its supported C/C++, ASM, Rust, Python, Java, C#, Kotlin, Swift, TypeScript/JavaScript, and Dart components from unified POSIX, Windows CMD, and PowerShell entry points plus CI.

**Architecture:** Keep one Python orchestration layer as the portable source of truth and expose thin `sh`, `.cmd`, and PowerShell wrappers. Use CMake/CTest for native targets, Cargo for Rust, language-native dependency/build tools for the other language trees, and CPack/package manifests for distributable installers. CI uses OS/architecture matrices and publishes versioned artifacts without silently installing privileged kernel/firmware components.

**Tech Stack:** Python 3.11+, CMake/CTest/CPack, Ninja or native generators, GCC/Clang/MSVC, NASM where required, Cargo/Rust, pip, npm, Maven/Gradle where present, dotnet, Kotlin/Swift/Dart toolchains, PowerShell 7, POSIX shell, Windows CMD, GitHub Actions.

**Spec:** Existing Chimera II OS build/installer capabilities and repository-wide language/toolchain requirements.

## Global Constraints

- Builds must be out-of-source and reproducible where toolchains permit.
- Dependency installation must be explicit, logged, and version-aware; never execute untrusted downloaded scripts.
- Kernel drivers, firmware, boot records, and destructive storage operations remain opt-in and separately authorized.
- Package metadata must preserve licenses and source provenance.
- CI must build/test before packaging and must not use `|| true` to hide packaging failures.
- The canonical build command must work from repository root on Linux/macOS and Windows PowerShell; CMD wrappers must delegate to the same orchestration logic.

---

### Task 1: Build/dependency inventory and failing automation contract

**Files:**
- Create: `tools/build/build_manifest.json`
- Create: `tests/build/test_build_manifest.py`
- Create: `docs/BUILD_INSTALL_AUTOMATION.md`

- [ ] Define supported language/toolchain entries, minimum versions, dependency commands, build commands, test commands, and artifact globs.
- [ ] Add tests requiring every supported language family to have a declared lifecycle and safety policy.
- [ ] Document host prerequisites, offline mode, cache directories, and failure semantics.

### Task 2: Portable Python build orchestrator

**Files:**
- Modify: `tools/build/main.py`
- Create: `tools/build/orchestrator.py`
- Create: `tools/build/dependencies.py`
- Create: `tools/build/package.py`
- Test: `tests/build/test_orchestrator.py`

- [ ] Add subcommands `doctor`, `deps`, `configure`, `build`, `test`, `package`, `install`, `clean`, and `all`.
- [ ] Add platform/architecture detection, dry-run, offline mode, parallelism, structured JSON logs, and deterministic artifact manifest generation.
- [ ] Implement allowlisted dependency installers for C/C++, Rust, Python, Java, .NET, Kotlin, Swift, Node/TypeScript, and Dart.
- [ ] Ensure commands are invoked without shell interpolation and fail with actionable diagnostics.

### Task 3: Native packaging and installers

**Files:**
- Modify: `CMakeLists.txt`
- Create: `cmake/ChimeraPackaging.cmake`
- Create: `packaging/README.md`
- Create: `packaging/chimera-install.json`
- Create: `packaging/windows/ChimeraIIOS.wxs`
- Create: `packaging/macos/ChimeraIIOS.bundle.json`
- Create: `packaging/linux/chimera.desktop`
- Test: `tests/installer/test_packaging_manifest.py`

- [ ] Add CPack configuration for TGZ/ZIP and native Linux package formats where available, plus NSIS/WiX hooks on Windows and macOS bundle/DMG hooks where available.
- [ ] Generate checksums and SBOM/provenance metadata alongside packages.
- [ ] Keep installer actions non-destructive by default and separate privileged boot/driver activation from package installation.

### Task 4: Shell/CMD/PowerShell entry points

**Files:**
- Create: `scripts/chimera-build.sh`
- Create: `scripts/chimera-build.cmd`
- Create: `scripts/chimera-build.ps1`
- Create: `scripts/chimera-install.sh`
- Create: `scripts/chimera-install.cmd`
- Create: `scripts/chimera-install.ps1`
- Modify: `tools/installer/chimera-installer.sh`
- Modify: `tools/installer/ChimeraInstaller.ps1`
- Test: `tests/scripts/test_entrypoints.py`

- [ ] Make wrappers forward arguments to the Python orchestrator, preserve exit codes, and support `--dry-run`.
- [ ] Add dependency bootstrap and toolchain doctor commands to every shell family.
- [ ] Keep existing installer scripts backward compatible while routing through the shared planner.

### Task 5: Language-specific build bridges

**Files:**
- Create: `tools/build/languages/python.py`
- Create: `tools/build/languages/rust.py`
- Create: `tools/build/languages/node.py`
- Create: `tools/build/languages/java.py`
- Create: `tools/build/languages/dotnet.py`
- Create: `tools/build/languages/kotlin.py`
- Create: `tools/build/languages/swift.py`
- Create: `tools/build/languages/dart.py`
- Create: `tools/build/languages/native.py`
- Test: `tests/build/test_language_bridges.py`

- [ ] Discover only language trees actually present in the repository.
- [ ] Prefer lockfiles/manifests already committed by the project and use offline/cache modes when requested.
- [ ] Emit one normalized artifact manifest independent of language.

### Task 6: CI/CD matrix and release artifacts

**Files:**
- Create: `.github/workflows/chimera-build-install-release.yml`
- Modify: `.github/workflows/build-release.yml`
- Create: `.github/workflows/chimera-toolchain-doctor.yml`
- Create: `docs/RELEASE_ARTIFACTS.md`

- [ ] Build/test on Linux, Windows, and macOS with x64/ARM64 where supported by hosted runners.
- [ ] Cache dependencies using language-native caches and GitHub Actions cache facilities.
- [ ] Package only after tests succeed; upload installers, archives, checksums, SBOM, and manifest.
- [ ] Keep Pages deployment independent from native package publication.

### Task 7: Verification and repository-wide documentation

**Files:**
- Modify: `README.md`
- Modify: `tools/installer/README.md` if present
- Modify: relevant `docs/*BUILD*`, `docs/*INSTALL*`, and ISO-Tool build documentation
- Create: `tests/build/test_repository_automation.py`

- [ ] Validate all wrapper references, workflow paths, package metadata, and manifest schemas.
- [ ] Run Python syntax/tests and native configure/build/test checks available in the environment.
- [ ] Inspect CI results and fix failures before declaring the automation complete.
