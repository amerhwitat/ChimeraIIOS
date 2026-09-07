# Aurora Wayland Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate Aurora Wayland as a structured, build-aware Chimera II userspace desktop subsystem with compositor scaffolding, shell services, themes/assets, localization, security documentation, packaging, and CI.

**Architecture:** Aurora lives under `userspace/aurora/` while the existing `desktop/aurora/` research implementation remains intact. The first milestone provides a conservative wlroots-based compositor foundation and clearly separates real integration code from research placeholders. Kore/Koronos integration is represented through manifests and service boundaries; privileged device access is never implemented by the desktop itself.

**Tech Stack:** C++17, CMake, wlroots, Wayland, libinput, libxkbcommon, Pango/Cairo where available, systemd/Kore manifests, GitHub Actions.

**Spec:** User-provided Aurora Wayland Desktop deliverables in the current conversation.

## Global Constraints

- Repository: `amerhwitat/ChimeraIIOS`, default branch `main`.
- Feature work begins on `feature/aurora-wayland-integration`.
- Existing Chimera II architecture and `desktop/aurora/` research code must not be deleted.
- Aurora is a research/engineering prototype, not a claim of production-ready wlroots compatibility.
- wlroots APIs vary by release; build logic must fail clearly when the selected API/dependency set is unsupported.
- Compositor execution is unprivileged; Kore is the intended privileged resource boundary.
- Arabic and English are first-class UI locales; RTL must be documented and testable.
- No hard-coded live weather or fabricated resource values in production widget interfaces.
- CI must distinguish dependency/build tests from tests requiring a graphical seat/GPU.

---

### Task 1: Repository integration skeleton

**Files:**
- Create: `userspace/aurora/README.md`
- Create: `userspace/aurora/compositor/CMakeLists.txt`
- Create: `userspace/aurora/compositor/include/aurora/compositor.hpp`
- Create: `userspace/aurora/compositor/src/main.cpp`
- Modify: `CMakeLists.txt`
- Test: CMake configure/build smoke test

**Interfaces:**
- Produces an independently configurable `aurora_compositor` target.
- Does not yet promise a functional desktop session.

- [ ] **Step 1: Add the subtree and build option**

Add an `AURORA_BUILD` CMake option defaulting to `OFF` so the existing C project remains buildable without wlroots development packages.

- [ ] **Step 2: Add the minimal executable and lifecycle API**

Implement `AuroraCompositor::init()`, `run()`, and `shutdown()` with explicit null-state handling.

- [ ] **Step 3: Configure without Aurora**

Run `cmake -S . -B build -DAURORA_BUILD=OFF && cmake --build build && ctest --test-dir build --output-on-failure`.

Expected: existing Chimera targets build and tests pass.

- [ ] **Step 4: Configure with Aurora when dependencies exist**

Run `cmake -S . -B build-aurora -DAURORA_BUILD=ON`.

Expected: either configure succeeds with detected dependencies or fails with a precise dependency/API message; it must not silently disable Aurora.

- [ ] **Step 5: Commit**

```bash
git add userspace/aurora CMakeLists.txt
git commit -m "feat: add Aurora Wayland userspace foundation"
```

---

### Task 2: Compositor core and shell boundaries

**Files:**
- Create: `userspace/aurora/compositor/include/aurora/shell.hpp`
- Create: `userspace/aurora/compositor/include/aurora/panel.hpp`
- Create: `userspace/aurora/compositor/include/aurora/launcher.hpp`
- Create: `userspace/aurora/compositor/src/compositor.cpp`
- Create: `userspace/aurora/compositor/src/shell.cpp`
- Create: `userspace/aurora/compositor/src/panel.cpp`
- Create: `userspace/aurora/compositor/src/launcher.cpp`

**Interfaces:**
- `AuroraShell` owns panel/launcher lifecycle.
- `AuroraLauncher::launch_desktop_entry(std::string_view)` validates an application identifier before delegating to a launcher backend.

- [ ] **Step 1: Add explicit wlroots resource ownership**

Create/destroy display, backend, renderer, and allocator in reverse ownership order. On any initialization failure, release already-created resources.

- [ ] **Step 2: Add shell service abstraction**

Keep xdg-shell/layer-shell registration behind `AuroraShell`; do not expose raw protocol ownership to widgets.

- [ ] **Step 3: Add launcher abstraction**

Do not invoke `gtk-launch` directly from the compositor core. Define a launcher backend interface that can later call Kore.

- [ ] **Step 4: Add build smoke tests**

Compile every Aurora translation unit when `AURORA_BUILD=ON` and ensure warnings are enabled.

- [ ] **Step 5: Commit**

```bash
git add userspace/aurora/compositor
git commit -m "feat: add Aurora compositor and shell boundaries"
```

---

### Task 3: Widgets, theme tokens, and localization

**Files:**
- Create: `userspace/aurora/compositor/include/aurora/widgets/clock.hpp`
- Create: `userspace/aurora/compositor/include/aurora/widgets/weather.hpp`
- Create: `userspace/aurora/compositor/include/aurora/widgets/resource_monitor.hpp`
- Create: corresponding `.cpp` files
- Create: `userspace/aurora/compositor/assets/themes/aurora-dark.css`
- Create: `userspace/aurora/compositor/assets/themes/aurora-high-contrast.css`
- Create: `docs/AURORA_LOCALIZATION.md`

**Interfaces:**
- Widgets return structured state instead of printing fabricated values.
- Clock consumes locale/timezone configuration.
- Weather consumes an injectable service interface.
- Resource monitor consumes an injectable metrics provider.

- [ ] **Step 1: Define widget state types**

Use explicit state structures so rendering is separated from acquisition.

- [ ] **Step 2: Implement clock state**

Use `std::chrono`/locale-aware formatting and expose direction metadata for Arabic RTL layouts.

- [ ] **Step 3: Implement weather provider boundary**

Default to an unavailable state until Kore/local weather data is supplied; never embed a fake current temperature.

- [ ] **Step 4: Implement resource metrics provider**

Read Linux `/proc` only behind a provider abstraction; return `unknown` when unavailable.

- [ ] **Step 5: Add theme tokens**

Preserve the supplied Aurora visual language: translucency, soft blue/warm accent, 10–16px radii, 48px panel and 64px dock baseline.

- [ ] **Step 6: Document gettext/Pango RTL strategy**

Document `ar` and `en` catalogs, Pango direction handling, fallback fonts, and keyboard navigation.

- [ ] **Step 7: Commit**

```bash
git add userspace/aurora/compositor/assets docs/AURORA_LOCALIZATION.md userspace/aurora/compositor/include userspace/aurora/compositor/src
git commit -m "feat: add Aurora widgets theme and localization foundations"
```

---

### Task 4: Kore/Koronos packaging and security model

**Files:**
- Create: `userspace/aurora/packaging/aurora.kore.json`
- Create: `userspace/aurora/packaging/aurora.service`
- Create: `userspace/aurora/packaging/aurora.desktop`
- Create: `docs/AURORA_SECURITY.md`

**Interfaces:**
- Kore manifest declares GPU/DRM/KMS capabilities without granting arbitrary privileges.
- Desktop launcher uses the Kore boundary rather than root execution.

- [ ] **Step 1: Add conservative service manifest**

Declare the compositor as an unprivileged service with only required graphical capabilities.

- [ ] **Step 2: Add systemd user service**

Do not combine system-wide and user-service semantics incorrectly; document the intended installation scope.

- [ ] **Step 3: Add desktop entry**

Use `aurora_compositor` as the executable and identify Aurora as a Wayland desktop/session component.

- [ ] **Step 4: Document DMA-BUF, DRM/KMS, input, sandboxing and portals**

Explicitly distinguish compositor privileges from application privileges.

- [ ] **Step 5: Commit**

```bash
git add userspace/aurora/packaging docs/AURORA_SECURITY.md
git commit -m "feat: integrate Aurora with Kore security boundaries"
```

---

### Task 5: Assets, demo, and documentation

**Files:**
- Create: `userspace/aurora/demo/README.md`
- Create: `userspace/aurora/compositor/assets/README.md`
- Create: `docs/AURORA_DESIGN.md`
- Create: `docs/AURORA_BUILD_RUN.md`
- Modify: `docs/IMAGE_ASSETS.md`

**Interfaces:**
- Documentation identifies generated artwork as design references unless the binary asset is actually present in Git.

- [ ] **Step 1: Add design specification**

Document palette tokens, spacing, typography, animation timing, dock/panel/launcher behavior, and accessibility requirements.

- [ ] **Step 2: Add build/run guide**

Provide Arch/Ubuntu dependency examples, nested compositor safety notes, TTY/session setup, Arabic locale test commands, and known wlroots-version caveats.

- [ ] **Step 3: Add asset provenance**

Separate generated project artwork from third-party icon sets and record licensing expectations.

- [ ] **Step 4: Add demo boundary**

Document a non-destructive GLFW/OpenGL preview that does not require it to masquerade as the actual compositor.

- [ ] **Step 5: Commit**

```bash
git add userspace/aurora docs
git commit -m "docs: add Aurora design build and asset documentation"
```

---

### Task 6: CI, packaging validation, and tests

**Files:**
- Create: `.github/workflows/aurora.yml`
- Create: `tests/aurora/test_widget_state.cpp`
- Create: `userspace/aurora/packaging/build_release.sh`
- Create: `userspace/aurora/packaging/flatpak/`

**Interfaces:**
- CI verifies source configuration and non-GPU build paths.
- Graphical compositor integration tests are explicitly marked as environment-dependent.

- [ ] **Step 1: Add deterministic widget tests**

Test clock formatting, unavailable weather state, and metrics-provider behavior with injected fixtures.

- [ ] **Step 2: Add Ubuntu CI dependency/build job**

Build with Aurora dependencies where available; preserve a core-only job for environments where wlroots is unavailable.

- [ ] **Step 3: Add packaging smoke validation**

Validate desktop/service/manifest syntax and package the source/assets without requiring a running display server.

- [ ] **Step 4: Add release script**

Package compositor source/binaries when built, documentation, manifests, and checksums. Never require GitHub credentials for the local package step.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/aurora.yml tests/aurora userspace/aurora/packaging
git commit -m "ci: add Aurora tests and packaging validation"
```

---

### Task 7: Final verification and integration PR

**Files:**
- Modify: `README.md`
- Modify: `docs/INTEGRATION_NOTES.md`

- [ ] **Step 1: Run core build/test**

```bash
cmake -S . -B build -DAURORA_BUILD=OFF
cmake --build build
ctest --test-dir build --output-on-failure
```

- [ ] **Step 2: Run Aurora build/test when dependencies are present**

```bash
cmake -S . -B build-aurora -DAURORA_BUILD=ON
cmake --build build-aurora
ctest --test-dir build-aurora --output-on-failure
```

- [ ] **Step 3: Inspect repository diff**

Confirm no existing Chimera subsystem was removed and no generated binary is represented as committed when it is not actually present.

- [ ] **Step 4: Update status documentation**

Record exactly which Aurora components build, which are research placeholders, and which require a real Wayland seat/GPU/Kore environment.

- [ ] **Step 5: Create a draft pull request**

Use `feature/aurora-wayland-integration` → `main` and include build/test evidence.

- [ ] **Step 6: Final verification**

Only claim completion after repository checks and available CI results substantiate the claim.
