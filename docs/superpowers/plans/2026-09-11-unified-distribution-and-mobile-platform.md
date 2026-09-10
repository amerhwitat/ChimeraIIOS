# Unified Distribution and Mobile Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn Chimera II OS into a reproducible all-in-one distribution with an offline-capable application catalog, Linux/Windows compatibility adapters, legitimate external-store integration, and a separately profiled Koronos Mobile platform for Android-class devices.

**Architecture:** Keep the ISO self-contained for open-source/core components while storing manifests, source references, build recipes, and launch adapters for proprietary applications rather than redistributing unauthorized binaries. Add a package-provider abstraction for Chimera native packages, Linux repositories/Flatpak/AppImage, Windows MSIX/EXE/MSI, and Android APK/AAB sources. Build mobile support around device profiles, AOSP/ACK/GKI interfaces, vendor modules, AVB/verified boot, and fastboot/recovery rather than claiming one image works on every handset.

**Tech Stack:** C/C++, shell, JSON, YAML, Python/Node/Java/.NET integration already present, GRUB/xorriso, GitHub Actions, AOSP/GKI-compatible kernel tooling, package manifests.

**Spec:** `docs/INSTALLATION_AND_BOOT.md`, `boot/README.md`, `installer/README.md`, and the approved architectural design in the conversation.

## Global Constraints

- One reproducible ISO must contain boot, installer, live environment, core runtime, application catalog, source manifests, and compatibility tooling.
- Proprietary application binaries are not redistributed unless their license permits it; use official distribution/store adapters instead.
- Destructive disk operations require explicit user confirmation and target identification.
- LILO is a compatibility/legacy path; Spit Fire and GRUB2 are primary boot paths.
- Mobile images are device-profile-specific and must not claim universal Samsung/Chinese-device compatibility.
- Android support must respect GKI/KMI, vendor modules, AVB, rollback protection, and bootloader state.
- Apple App Store applications cannot be represented as universally installable on Chimera; provide lawful catalog/store/web/PWA adapters where possible.
- Every generated ISO artifact must be reproducible and SHA-256 hashed by CI.

---

### Task 1: Application provider model

**Files:**
- Create: `appcenter/schema/chimera-app.schema.json`
- Create: `appcenter/catalog/apps.json`
- Create: `appcenter/README.md`

- [ ] Define a stable manifest containing id, name, category, license, source URL, provider, architectures, package formats, sandbox policy, and install strategy.
- [ ] Add initial catalog entries for YouTube/PWA, Chromium/Firefox, VLC, Telegram, Signal, Discord, Reddit, LibreOffice, GIMP, VS Code-compatible editor, and common system tools, marking proprietary entries as external-source adapters.
- [ ] Document license and provenance requirements.
- [ ] Validate JSON with a CI test.

### Task 2: Linux and Windows provider adapters

**Files:**
- Create: `appcenter/providers/linux.json`
- Create: `appcenter/providers/windows.json`
- Create: `appcenter/providers/android.json`
- Create: `appcenter/providers/apple.json`
- Create: `appcenter/providers/flatpak.json`
- Create: `appcenter/providers/appimage.json`
- Create: `appcenter/providers/native.json`

- [ ] Encode provider capabilities and official endpoints without embedding third-party binaries.
- [ ] Support Linux package metadata, Flatpak remotes, AppImage artifacts, Windows MSIX/AppX and EXE/MSI, and Android APK/AAB metadata.
- [ ] Make Apple entries explicitly catalog/store/web/PWA oriented unless a platform-specific signed distribution is available.

### Task 3: Unified App Center CLI/runtime

**Files:**
- Create: `appcenter/cli/chimera-appctl.py`
- Create: `appcenter/cli/README.md`
- Create: `appcenter/tests/test_catalog.py`

- [ ] Implement `list`, `search`, `show`, `sources`, `install-plan`, and `verify` operations.
- [ ] Make `install-plan` output a deterministic plan without executing destructive operations.
- [ ] Verify manifest checksums and HTTPS source policy where applicable.
- [ ] Add tests for catalog parsing and provider selection.

### Task 4: ISO integration

**Files:**
- Modify: `boot/iso/build-iso.sh`
- Modify: `.github/workflows/chimera-iso.yml`
- Create: `iso/README.md`
- Create: `iso/manifests/core-packages.txt`
- Create: `iso/manifests/application-catalog.txt`

- [ ] Copy application catalog/providers/source manifests into the ISO tree.
- [ ] Include the installer, live environment, boot menus, native runtime scaffolding, and application manager.
- [ ] Add ISO smoke checks for required files and boot configuration.
- [ ] Preserve SHA-256 generation and artifact upload.

### Task 5: Linux/Windows source and build integration

**Files:**
- Create: `platform/linux/README.md`
- Create: `platform/linux/build.sh`
- Create: `platform/windows/README.md`
- Create: `platform/windows/build.ps1`
- Create: `platform/windows/app-manifest.md`

- [ ] Document Linux-targeted native builds and Windows-targeted builds.
- [ ] Make Windows packaging compatible with MSIX and traditional EXE/MSI workflows.
- [ ] Keep current .NET support claims limited to actually supported Windows versions.

### Task 6: Koronos Mobile architecture

**Files:**
- Create: `mobile/README.md`
- Create: `mobile/architecture.md`
- Create: `mobile/device-profile.schema.json`
- Create: `mobile/device-profiles/reference-aarch64.json`
- Create: `mobile/device-profiles/qualcomm-generic.json`
- Create: `mobile/device-profiles/mediatek-generic.json`
- Create: `mobile/device-profiles/samsung-generic.json`
- Create: `mobile/boot/README.md`
- Create: `mobile/kernel/README.md`

- [ ] Define device profile fields for SoC, boot protocol, partitions, display, storage, radio, GPU, AVB, GKI/KMI, and vendor modules.
- [ ] Separate generic Koronos Mobile code from device-specific vendor integration.
- [ ] Document fastboot/recovery/A-B flashing requirements and rollback/recovery strategy.

### Task 7: Mobile image build scaffolding

**Files:**
- Create: `mobile/build/build-mobile-image.sh`
- Create: `mobile/build/validate-profile.py`
- Create: `mobile/images/README.md`
- Create: `mobile/flash/README.md`
- Create: `.github/workflows/chimera-mobile.yml`

- [ ] Validate profiles before image construction.
- [ ] Build a reproducible research image layout rather than pretending to produce a universal phone image.
- [ ] Add fastboot/recovery packaging hooks and AVB/signing placeholders that fail safely when required signing material is absent.
- [ ] Add CI validation for profiles and scripts.

### Task 8: Documentation and verification

**Files:**
- Modify: `README.md`
- Modify: `docs/INSTALLATION_AND_BOOT.md`
- Create: `docs/APPLICATION_ECOSYSTEM.md`
- Create: `docs/MOBILE_PORTING_MATRIX.md`
- Create: `docs/LEGAL_AND_PROVENANCE.md`

- [ ] Document what is bundled, what is fetched from official sources, and what requires user authorization.
- [ ] Document Apple, Microsoft, Linux, Flatpak, Android, and mobile constraints.
- [ ] Add reproducibility and verification instructions.
- [ ] Run JSON, Python, shell syntax, and repository-content checks before claiming completion.
