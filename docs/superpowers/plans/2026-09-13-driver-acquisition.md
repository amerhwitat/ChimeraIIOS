# Chimera II Driver Acquisition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a secure capability for Chimera II OS to discover, acquire, verify, stage, and adapt Linux and Windows driver packages without blindly installing incompatible or unsigned kernel code.

**Architecture:** Chimera uses a driver-acquisition broker with source allowlists, hardware-ID matching, package metadata, SHA-256 verification, license/provenance records, signature/trust policy, sandboxed extraction, and explicit installation authorization. Linux packages are treated as source/module/adapter candidates because Linux kernel modules are kernel-version/ABI specific; Windows packages are treated as INF/CAT/driver bundles and require Windows-compatible signing/staging rules. A Java implementation mirrors the portable acquisition model.

**Tech Stack:** C11/C++, Python, Java 17+, JSON, SHA-256, HTTPS-capable external fetch adapters, GitHub Actions.

**Spec:** `docs/DRIVER_ARCHITECTURE.md`, `docs/DRIVER_WINDOWS_LINUX_UNIX.md`, `drivers/hardware_registry.json`

## Global Constraints

- Never silently install a kernel driver or firmware.
- Never disable Secure Boot, signature enforcement, or platform security to load a driver.
- Never redistribute proprietary Windows/vendor driver binaries without a license permitting redistribution.
- Preserve SPDX/license and source provenance metadata for imported open-source source.
- Verify SHA-256 before accepting a downloaded artifact.
- Match artifacts against hardware IDs and architecture before staging.
- Keep acquisition separate from installation so the user/kernel policy can approve the final operation.

---

### Task 1: Acquisition policy tests

**Files:**
- Create: `drivers/tests/test_driver_acquisition_policy.py`

- [ ] Write tests for allowlisted source URLs, SHA-256 verification, hardware-ID mismatch rejection, unsigned Windows package rejection under strict policy, and Linux module ABI mismatch rejection.
- [ ] Run the Python test suite and confirm the new tests fail because the acquisition policy module does not yet exist.

### Task 2: Portable acquisition broker

**Files:**
- Create: `drivers/python/driver_acquisition.py`
- Create: `drivers/acquisition_sources.json`
- Modify: `drivers/README.md`

- [ ] Implement `DriverArtifact`, `HardwareMatch`, `AcquisitionPolicy`, `verify_sha256()`, `match_hardware()`, and `stage_artifact()`.
- [ ] Support Linux source/package/module metadata and Windows INF/CAT/SYS metadata without executing downloaded code.
- [ ] Enforce HTTPS and source allowlists.
- [ ] Verify SHA-256 and optional signature metadata before staging.
- [ ] Return a structured acquisition result instead of invoking a kernel loader.
- [ ] Run the tests and make them pass.

### Task 3: Java driver acquisition implementation

**Files:**
- Create: `java/chimera/drivers/acquisition/DriverArtifact.java`
- Create: `java/chimera/drivers/acquisition/AcquisitionPolicy.java`
- Create: `java/chimera/drivers/acquisition/DriverAcquisitionManager.java`
- Create: `java/chimera/drivers/acquisition/DriverAcquisitionResult.java`
- Create: `java/chimera/drivers/hardware/HardwareId.java`
- Create: `java/chimera/drivers/acquisition/DriverAcquisitionManagerTest.java`
- Create: `java/README.md`

- [ ] Add SHA-256 verification, HTTPS/source allowlist checks, hardware-ID matching, and package-type validation.
- [ ] Keep installation disabled by default and expose acquisition/staging as separate operations.
- [ ] Add Java tests for deterministic matching and checksum rejection.
- [ ] Compile the Java source in CI.

### Task 4: Linux/Windows native adapter boundaries

**Files:**
- Create: `drivers/linux/chimera_driver_acquisition.c`
- Create: `drivers/windows/chimera_driver_acquisition.c`
- Create: `drivers/c/chm_driver_acquisition.h`
- Modify: `docs/DRIVER_WINDOWS_LINUX_UNIX.md`
- Create: `docs/DRIVER_ACQUISITION.md`

- [ ] Define C ABI structures for discovery, verification, staging, and policy decisions.
- [ ] Linux adapter discovers compatible source/module/package candidates but does not assume Linux modules can be loaded into Koronos.
- [ ] Windows adapter recognizes INF/CAT/SYS package structure and delegates trusted staging to the native Windows installation mechanisms when running on Windows.
- [ ] Document Windows Driver Store signing/staging requirements and Linux kernel ABI constraints.

### Task 5: Registry/update automation

**Files:**
- Create: `tools/update_driver_sources.py`
- Create: `.github/workflows/driver-acquisition-metadata.yml`
- Modify: `docs/HARDWARE_DRIVER_SOURCE_PROVENANCE.md`

- [ ] Generate acquisition metadata from curated official/open-source source definitions.
- [ ] Make metadata updates deterministic and reviewable.
- [ ] Do not download or execute driver binaries during ordinary CI.
- [ ] Validate JSON schemas and provenance records.

### Task 6: Documentation and verification

**Files:**
- Modify: `README.md`
- Modify: `drivers/README.md`
- Modify: `docs/DRIVER_ARCHITECTURE.md`

- [ ] Document the complete acquisition flow: detect -> search -> rank -> download -> verify -> license/provenance -> sandbox -> stage -> explicit install.
- [ ] Run Python tests and Java compilation/tests.
- [ ] Compile the native acquisition adapters where toolchains are available.
- [ ] Verify GitHub Actions workflow syntax and report only verified results.
