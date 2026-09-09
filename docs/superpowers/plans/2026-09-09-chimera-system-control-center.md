# Chimera System Control Center Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a professional unified Control Center for Aurora/Web with process and service management, settings/preferences, desktop/session controls, and detailed health KPIs.

**Architecture:** `web/system_control_center.html` is the canonical browser UI. `web/system_control_center.js` owns state, capability-aware API calls, polling, settings persistence, confirmation flows, and rendering. `web/system_control_center.json` defines the stable contract for processes/services/KPIs/settings/actions; destructive actions require an authorized native/session adapter and otherwise remain disabled/read-only. Aurora integrates the Control Center through the taskbar/dock and application registry; CPU4096Simulator consumes the same contract with a local web adapter. Other integrated repositories receive a small manifest pointing at the canonical contract rather than duplicating management logic.

**Tech Stack:** HTML5, CSS, vanilla JavaScript, JSON contract, localStorage, optional `/api/system/*` native backend, GitHub repository content.

**Spec:** `docs/superpowers/specs/2026-09-09-chimera-system-control-center-design.md`

## Global Constraints

- Browser-only mode must not claim native process/service control.
- Native process/service actions require an explicit authorized backend/capability.
- Destructive operations require confirmation and must expose result/error state.
- Health metrics must distinguish native, emulated, browser, unavailable, and unknown sources.
- Settings are namespaced under `chimera.*` and remain local unless a backend explicitly persists them.
- Aurora remains the default desktop profile.
- Linux desktop profiles and Windows profiles remain session adapters/web profiles unless a real authorized backend exists.
- No credentials, secrets, ROMs, firmware, or proprietary system binaries are embedded.

---

### Task 1: Control Center contract and conformance tests

**Files:**
- Create: `web/system_control_center.json`
- Create: `web/tests/system_control_center.test.mjs`

**Interfaces:**
- Produces schema `chimera-system-control-center/v1` with `capabilities`, `processes`, `services`, `kpis`, `settings`, and `actions` definitions.
- Action IDs: `process.stop`, `process.kill`, `service.start`, `service.stop`, `service.restart`, `service.enable`, `service.disable`, `system.shutdown`, `system.reboot`.

- [ ] **Step 1: Write the failing test**

Test that the contract exists, has all required sections, stable action IDs, source/status fields, and settings categories.

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test web/tests/system_control_center.test.mjs`
Expected: FAIL because `web/system_control_center.json` does not yet exist.

- [ ] **Step 3: Write minimal contract**

Define the schema, capability flags, process/service fields, KPI fields (`value`, `unit`, `status`, `source`, `timestamp`, `confidence`), and settings keys.

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test web/tests/system_control_center.test.mjs`
Expected: PASS.

- [ ] **Step 5: Commit**

Commit: `feat(control-center): add system management contract`

---

### Task 2: Control Center UI and state engine

**Files:**
- Create: `web/system_control_center.html`
- Create: `web/system_control_center.js`
- Create: `web/system_control_center.css`

**Interfaces:**
- Consumes `system_control_center.json`.
- Reads `/api/system/overview`, `/api/system/processes`, `/api/system/services`, `/api/system/kpis`, `/api/system/settings` when available.
- Writes action requests to `/api/system/action` only when the advertised capability is enabled.
- Uses localStorage keys `chimera.control.settings`, `chimera.desktop.profile`.

- [ ] **Step 1: Write failing UI assertions**

Extend `web/tests/system_control_center.test.mjs` to require the UI files and verify the named sections and action hooks exist.

- [ ] **Step 2: Run test and verify failure**

Run: `node --test web/tests/system_control_center.test.mjs`
Expected: FAIL because UI files do not exist.

- [ ] **Step 3: Implement UI**

Build a responsive glass utility with Overview, Processes, Services, Performance/KPIs, Settings & Preferences, Desktop & Sessions, Startup, and Recovery tabs. Include search/filter/sort, status badges, compact resource meters, action menus, confirmation dialogs, backend/source badges, and explicit read-only states.

- [ ] **Step 4: Run tests**

Run: `node --test web/tests/system_control_center.test.mjs`
Expected: PASS.

- [ ] **Step 5: Commit**

Commit: `feat(control-center): add professional management desktop`

---

### Task 3: Aurora taskbar/dock and application integration

**Files:**
- Modify: `web/aurora_apps.json`
- Modify: `web/aurora_shell.js`
- Modify: `web/aurora_shell.css`
- Modify: `web/index.html`

**Interfaces:**
- Application ID: `system-control-center`.
- Dock shortcut label: `System Control Center`.
- The taskbar shortcut opens `system_control_center.html` in a dedicated application window.
- Active desktop profile remains synchronized through `chimera.desktop.profile`.

- [ ] **Step 1: Add failing registry assertions**

Require the Control Center app, System category placement, and a taskbar/dock shortcut in the shell source.

- [ ] **Step 2: Run test and verify failure**

Run: `node --test web/tests/system_control_center.test.mjs`
Expected: FAIL until the registry/shell contain the new integration.

- [ ] **Step 3: Implement registry and dock integration**

Add the app entry, place a dedicated Control Center button beside the desktop switcher, and preserve all existing application behavior.

- [ ] **Step 4: Run tests**

Run: `node --test web/tests/system_control_center.test.mjs`
Expected: PASS.

- [ ] **Step 5: Commit**

Commit: `feat(aurora): add control center to taskbar and launcher`

---

### Task 4: CPU4096Simulator integration

**Files:**
- Create/modify: `public/system_control_center.json`
- Create/modify: `public/system_control_center.html`
- Create/modify: `public/system_control_center.js`
- Modify: `public/aurora_apps.json`
- Modify: `public/aurora_shell.js`
- Modify: `test/desktop-retro-catalog.test.mjs`

**Interfaces:**
- Uses the same schema/action IDs as ChimeraIIOS.
- Browser simulator mode reports simulated process/service/KPI data and never labels it native.

- [ ] **Step 1: Add failing simulator assertions**

Require the canonical contract, Control Center page, and registry entry.

- [ ] **Step 2: Run test and verify failure**

Run the repository's Node test command and confirm the new assertions fail.

- [ ] **Step 3: Implement simulator adapter/UI**

Use deterministic simulated rows and clearly label the backend `simulated`.

- [ ] **Step 4: Run tests**

Run the repository's available Node test suite and verify the new assertions pass.

- [ ] **Step 5: Commit**

Commit: `feat(simulator): integrate system control center`

---

### Task 5: Cross-repository integration manifests

**Files:**
- Modify: `aurora_integration.json` in `CPU4096`, `nlp`, `PDFreaderPY`, `bruteforce`, `amerhwitat.github.io`, `general`, `BizX`, `BizXtreme`, `test`, `keygen` where present.

**Interfaces:**
- Each manifest points to the canonical Control Center contract and UI in ChimeraIIOS.
- No repository receives unsafe unrestricted native process control merely by consuming the manifest.

- [ ] **Step 1: Add failing manifest checks where repository tests exist**

Require `system_control_center.json` canonical references.

- [ ] **Step 2: Verify failure**

Run repository-specific lightweight checks where available.

- [ ] **Step 3: Update manifests**

Add `system_control_center_contract`, `system_control_center_ui`, and capability notes.

- [ ] **Step 4: Verify**

Fetch the updated manifests and validate their JSON structure.

- [ ] **Step 5: Commit**

Commit each repository update with `feat(aurora): integrate system control center contract`.

---

### Task 6: Documentation and verification

**Files:**
- Create: `docs/system-control-center.md`
- Modify: `README.md` if a relevant feature index exists.

**Interfaces:**
- Documents UI sections, API contract, capability model, security boundary, and Linux/Windows adapter expectations.

- [ ] **Step 1: Write documentation**

Document the browser-only versus native-backed modes and every supported management action.

- [ ] **Step 2: Run validation**

Run JSON parsing, Node tests, and repository status checks. Verify the Control Center files are reachable from the default branch.

- [ ] **Step 3: Commit**

Commit: `docs(control-center): document system management architecture`

- [ ] **Step 4: Final verification**

Inspect the resulting commits and changed files; report exactly which repositories were updated and which native operations remain adapter-dependent.
