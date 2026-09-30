# Native Chimera II Boot and Enterprise Services Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved native Chimera II boot/service architecture so Spit Fire→Jasper→Koronos→Kore→Aurora supports recovery modes, hardware-aware service activation, installer/runtime enterprise-service selection, and shared service metadata.

**Architecture:** Spit Fire performs firmware handoff, Jasper selects boot policy/mode, Koronos publishes hardware capability state, Kore resolves and supervises services, and Aurora consumes the same registry for installation and runtime administration. Service definitions are declarative metadata with a generated dependency graph; privileged runtime changes go through Kore.

**Tech Stack:** C++17 freestanding Koronos, POSIX-hosted test utilities, Bash ISO/installer tooling, JSON/YAML metadata, Aurora runtime, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-30-native-boot-services-design.md`

## Global Constraints
- Preserve `UEFI/BIOS -> Spit Fire -> Jasper -> Koronos early kernel -> Koronos core -> Kore -> Aurora Session -> Aurora Desktop`.
- Support Normal, Recovery, Safe Mode, Last Known Good, Live Aurora, Installer, Diagnostics, and configured chain-loader entries.
- Do not introduce proprietary Windows/macOS code or proprietary driver binaries without redistribution rights.
- Privileged service mutation remains policy-controlled by Kore.
- Installer, Kore, and Aurora consume one service source of truth.
- Optional enterprise services/games remain modular and are not forced into Live media.
- New boot/service features require automated host-side validation before ISO integration.

## Review Focus
- Malformed/cyclic dependencies fail closed — Task 2 tests.
- Missing optional hardware selects safe fallback — Task 3 tests.
- Critical vs optional service failure has distinct recovery behavior — Task 2/4 tests.
- Invalid/untrusted installer selections cannot silently enable privileged services — Task 5 tests.
- Recovery remains usable when Aurora/enterprise services fail — Task 4/6 tests.

---

### Task 1: Shared Service Registry and Profiles
**Files:** Create `config/services/service-registry.json`, `service-profiles.json`, `hardware-requirements.json`, `security-policies.json`, `dependency-graph.json`; create `tools/tests/test_service_registry.py`.
**Interfaces:** Registry schema `chimera-service-registry-v1`; profile schema `chimera-service-profile-v1`.
- [ ] Write failing tests for schema, unique IDs, dependency references, and profile expansion.
- [ ] Run `python3 tools/tests/test_service_registry.py` and confirm failure.
- [ ] Add core boot, storage/network/security, Aurora, developer, database, web, file/network, virtualization/container, AI/ML, monitoring, backup, and remote-management entries with explicit implementation states.
- [ ] Add the 15 installer profiles from the specification.
- [ ] Add hardware requirements and least-privilege policies.
- [ ] Validate the dependency graph and reject cycles/dangling references.
- [ ] Commit `feat: add shared Chimera service registry and profiles`.

### Task 2: Kore Service Graph and State Model
**Files:** Modify existing Kore/service bootstrap sources; create/modify `kernel/include/chimera_service.h`; create `tools/tests/test_kore_service_graph.py`.
**Interfaces:** `chimera_service_validate(const ChimeraServiceManifest*, size_t)`; `chimera_service_resolve(const ChimeraServiceGraph*, ChimeraServicePlan*)`; states `DECLARED/BLOCKED/STARTING/RUNNING/STOPPING/STOPPED/FAILED/RECOVERING`.
- [ ] Write tests for dependency ordering, cycle rejection, optional failure isolation, restart policy, and deterministic ordering.
- [ ] Verify tests fail before implementation.
- [ ] Implement validation/topological resolution without dynamic allocation in early freestanding boot.
- [ ] Implement state transitions, health checks, restart policy, and failure attribution through existing IPC/logging.
- [ ] Run host tests and `kernel/build-koronos.sh`.
- [ ] Verify required symbols remain linked and no hosted libc dependency is introduced.
- [ ] Commit `feat: add Kore dependency-aware service orchestration`.

### Task 3: Koronos Hardware Capability Contract
**Files:** Modify `kernel/core/hardware.cpp`, `device.cpp`, `driver.cpp`; create `kernel/include/chimera_hardware_profile.h`; create `tools/tests/test_hardware_profile.py`.
**Interfaces:** `chimera_hardware_profile_init(ChimeraHardwareProfile*)`; `chimera_hardware_profile_publish(const ChimeraHardwareProfile*)`; `chimera_driver_select(const ChimeraHardwareProfile*, const ChimeraDriverCatalog*, ChimeraDriverSelection*)`.
- [ ] Write tests for x86_64/ARM64 metadata, absent devices, graphics APIs, TPM, and generic fallback.
- [ ] Verify tests fail.
- [ ] Implement profile from existing firmware/device enumeration.
- [ ] Implement driver selection order: native Chimera, compatible open, explicitly licensed compatibility, generic safe driver.
- [ ] Integrate profile with Kore requirements.
- [ ] Run Koronos build/symbol checks.
- [ ] Commit `feat: publish Koronos hardware capability profile`.

### Task 4: Jasper Boot Modes and Recovery
**Files:** Modify existing Jasper/Spit Fire boot configuration; create `boot/chimera-boot-modes.json`; create `tools/tests/test_boot_modes.py`.
**Interfaces:** mode IDs `normal`, `recovery`, `safe-mode`, `last-known-good`, `live-aurora`, `installer`, `diagnostics`, `chainloader`.
- [ ] Test every mode and reject duplicate IDs/missing targets.
- [ ] Verify tests fail.
- [ ] Add boot-mode registry and Jasper mapping.
- [ ] Record Last Known Good only after a successful Kore/Aurora health checkpoint.
- [ ] Add critical-startup recovery fallback.
- [ ] Validate boot configuration and artifact references.
- [ ] Commit `feat: add native boot modes and recovery policy`.

### Task 5: Installer Enterprise-Service Selection
**Files:** Modify existing installer GUI/controller; create `installer/services/service-selection.json`; create `tools/tests/test_installer_service_selection.py`.
**Interfaces:** `expand_service_profile(profile_id, requested_services, registry) -> InstallPlan`; `validate_install_plan(plan, hardware_profile, security_policy) -> ValidationResult`.
- [ ] Test all profiles, dependency expansion, hardware incompatibility, privileged confirmation, and invalid selections.
- [ ] Verify tests fail.
- [ ] Implement selection using shared registry.
- [ ] Add profile plus advanced-service UI state.
- [ ] Persist the plan into target `/etc/chimera/services/`.
- [ ] Run installer validation.
- [ ] Commit `feat: add enterprise service selection to installer`.

### Task 6: Aurora Runtime Service Center
**Files:** Modify existing Aurora settings/service sources; create `desktop/aurora/services/service-center.md` and runtime adapter; create `tools/tests/test_aurora_service_policy.py`.
**Interfaces:** `list_services()`; `start_service(id)`; `stop_service(id)`; `restart_service(id)`; `enable_service(id)`; `disable_service(id)`, all through Kore IPC.
- [ ] Test authorization, failed-service display, dependency-aware operations, and unavailable services.
- [ ] Verify tests fail.
- [ ] Implement Kore client/IPC adapter.
- [ ] Add Installed/Available/Running/Stopped/Failed/Startup/Dependencies/Logs/Enterprise views.
- [ ] Add audit records for privileged changes.
- [ ] Run Aurora host tests.
- [ ] Commit `feat: add Aurora service center backed by Kore`.

### Task 7: Secure/Measured Boot and Journal
**Files:** Modify Spit Fire/Jasper trust/measurement sources; create `boot/chimera-measurement-policy.json`; create `tools/tests/test_boot_measurements.py`.
**Interfaces:** measurement records contain stage, artifact, digest, verification result, and failure reason.
- [ ] Test development mode, secure verification, missing TPM, digest mismatch, and recovery routing.
- [ ] Verify tests fail.
- [ ] Implement capability-gated measurement; missing TPM uses documented non-TPM behavior.
- [ ] Add trusted metadata checks for boot-critical manifests.
- [ ] Route verification failures to Jasper recovery and boot journal.
- [ ] Run host validation and artifact checks.
- [ ] Commit `feat: add trusted boot measurement policy`.

### Task 8: ISO, Live Media, CI and End-to-End Tests
**Files:** Modify `build-chimera-iso.sh`; create/modify `.github/workflows/chimera-boot-services.yml`; create `tools/tests/test_iso_service_integration.py`.
**Interfaces:** ISO builder validates registry, profiles, dependency graph, boot modes, hardware requirements, and security policy before final image creation.
- [ ] Test invalid manifests and optional-service exclusion from Live media.
- [ ] Verify tests fail.
- [ ] Add validation/staging checkpoint before SquashFS generation.
- [ ] Stage `/etc/chimera/services/` and boot-mode metadata into targets.
- [ ] Add CI for shell syntax, JSON validation, service tests, Koronos build, and ISO manifest validation.
- [ ] Run `bash -n build-chimera-iso.sh` and all available tests.
- [ ] Verify SquashFS remains fresh-build/`-noappend` behavior.
- [ ] Commit `feat: integrate boot services into ISO and CI`.

### Final Verification
- [ ] Run the complete host-side suite.
- [ ] Build Koronos ELF64 and existing N-bit artifacts.
- [ ] Validate all boot/service metadata.
- [ ] Build ISO and verify Live/Installer/Recovery entries.
- [ ] Inspect boot logs for Spit Fire→Jasper→Koronos→Kore→Aurora attribution.
- [ ] Run QEMU smoke tests for supported boot modes.
- [ ] Confirm no proprietary driver/code/assets were introduced.
- [ ] Record verification results before claiming completion.
