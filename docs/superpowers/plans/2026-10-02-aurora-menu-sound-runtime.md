# Aurora Menu, Sound, Initialization Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved Aurora initialization video, Koronos-driven progress UI, centralized menu sound/event system, installer/Live-CD/recovery integration, and safe Docker publication without making multimedia a boot dependency.

**Architecture:** Canonical Aurora assets live under `desktop/aurora/assets`; one event API maps menu/system events to optional audio assets. Koronos/boot services publish progress through a small state file/IPC-compatible contract consumed by Aurora and installer UIs. `build-chimera-iso.sh` stages the canonical assets and validates them; Docker publishing is explicit by environment/flag and never embeds credentials.

**Tech Stack:** Bash, JSON, C/C++ boot/runtime components, Wayland/Aurora shell, xorriso/grub-mkrescue, Docker/BuildKit, FFmpeg where available.

**Spec:** `docs/superpowers/specs/2026-10-02-aurora-menu-features-sound-design.md`

## Global Constraints

- Multimedia must never be required for BIOS/UEFI boot, recovery, or text installation.
- Missing audio/video devices fall back silently to functional UI.
- `init.mp4` is canonical and must not be duplicated unnecessarily.
- Koronos progress is authoritative; UI must not fabricate completion percentages.
- Menu actions must have functional handlers and safe cancel/back paths.
- Docker credentials must come only from environment/CI secrets and never be committed.
- ISO verification must cover BIOS/UEFI El Torito paths and critical boot artifacts.

## Review Focus

- Missing media/player: Aurora and installer continue without blocking.
- Corrupt/absent progress state: UI shows indeterminate state without inventing progress.
- Arabic RTL/input: menu navigation and labels remain usable.
- Broken asset links: build fails early with a useful diagnostic rather than producing a broken ISO.
- Docker unauthenticated/offline build: local image build succeeds without attempting credential leakage.

### Task 1: Canonical Aurora media/event assets

**Files:**
- Create: `desktop/aurora/assets/init.mp4` (generated binary)
- Create: `desktop/aurora/assets/sounds/manifest.json`
- Create: `desktop/aurora/assets/sounds/README.md`

**Interfaces:**
- Produces canonical `init.mp4` and sound-event manifest consumed by later tasks.

- [ ] Generate a short silent-safe Aurora initialization MP4 from canonical Aurora artwork with no external runtime dependency.
- [ ] Define event names for startup, menu-open, focus, select, back, cancel, warning, error, success, device-connect, device-disconnect, install-step, recovery, shutdown.
- [ ] Document optional audio policy and fallback behavior.
- [ ] Validate MP4 container/codec with `ffprobe` when available.
- [ ] Commit assets and manifest.

### Task 2: Aurora event/sound service

**Files:**
- Create: `desktop/aurora/aurora-event-sound.sh`
- Create: `desktop/aurora/aurora-menu-events.json`
- Test: `tools/tests/test-aurora-events.sh`

**Interfaces:**
- `aurora-event-sound.sh EVENT [volume]` returns success even when audio is unavailable.
- Consumes `desktop/aurora/assets/sounds/manifest.json`.

- [ ] Write shell tests for known events, unknown events, no-player fallback, and disabled-sound mode.
- [ ] Implement player detection (`pw-play`, `paplay`, `aplay`, `ffplay`) with timeout and no-fail behavior.
- [ ] Implement event mapping and rate limiting for focus/hover sounds.
- [ ] Add `CHIMERA_SOUND_ENABLED=0` and reduced-motion/accessibility handling.
- [ ] Run tests and commit.

### Task 3: Koronos initialization progress contract

**Files:**
- Create: `system/boot/koronos-progress.sh`
- Create: `config/boot/koronos-progress.json`
- Test: `tools/tests/test-koronos-progress.sh`

**Interfaces:**
- `koronos-progress.sh set <percent> <phase> <message>` writes an atomic state file.
- `koronos-progress.sh get` emits machine-readable state.

- [ ] Test monotonic phase updates and malformed input rejection.
- [ ] Implement atomic writes with sequence/timestamp.
- [ ] Define phases for CPU, memory, interrupts, scheduler, IPC, devices, storage, network, services, Aurora.
- [ ] Add compatibility for text-mode consumers.
- [ ] Run tests and commit.

### Task 4: Aurora splash and progress integration

**Files:**
- Create: `desktop/aurora/aurora-init-splash.sh`
- Modify: existing Aurora startup script discovered during implementation.
- Modify: existing Aurora progress script discovered during implementation.
- Test: `tools/tests/test-aurora-splash.sh`

**Interfaces:**
- Splash accepts the canonical `init.mp4` path and progress state path.
- Startup continues when video player is unavailable.

- [ ] Test missing video/player fallback.
- [ ] Implement splash launch with graceful fallback and termination before desktop takeover.
- [ ] Overlay Koronos progress and phase text using the existing progress mechanism.
- [ ] Ensure no splash process survives into shutdown or recovery transition.
- [ ] Run tests and commit.

### Task 5: Menu feature/event integration

**Files:**
- Modify: Aurora menu/configuration files discovered during implementation.
- Create: `desktop/aurora/menu-event-map.json`
- Test: `tools/tests/test-menu-event-map.sh`

**Interfaces:**
- Menu actions emit standardized events and preserve Back/Cancel/Retry/Continue semantics.

- [ ] Test every defined event has a manifest mapping or explicit silent fallback.
- [ ] Integrate events across boot, installer, Live CD, recovery, diagnostics, power, network, storage, driver and settings menus.
- [ ] Add keyboard/mouse/touch-safe event hooks without making sound mandatory.
- [ ] Add RTL-safe labels and accessibility/reduced-motion hooks where existing menu infrastructure supports them.
- [ ] Run tests and commit.

### Task 6: Installer/Live-CD/recovery visual progress

**Files:**
- Modify: installer staging/runtime scripts discovered during implementation.
- Modify: live/recovery runtime staging scripts discovered during implementation.
- Create: `config/ui/progress-events.json`

**Interfaces:**
- All graphical/text interfaces consume the same Koronos progress state.

- [ ] Test progress state is readable from installer, Live CD and recovery roots.
- [ ] Stage `init.mp4` as an optional GUI background.
- [ ] Add phase/progress overlays and sound events.
- [ ] Preserve pure-text fallback.
- [ ] Run tests and commit.

### Task 7: ISO build staging and validation

**Files:**
- Modify: `build-chimera-iso.sh`
- Create: `tools/validate-aurora-assets.sh`
- Test: `tools/tests/test-build-assets.sh`

**Interfaces:**
- Builder stages canonical Aurora assets under `/usr/share/chimera/aurora/assets` and validates links/media before ISO generation.

- [ ] Test staging with missing optional media and required configuration.
- [ ] Add canonical asset staging after rootfs/features preparation.
- [ ] Validate relative links, MP4 readability when tools exist, and manifest references.
- [ ] Keep boot-critical files as regular files.
- [ ] Run shell syntax tests and commit.

### Task 8: Docker build/publish pipeline

**Files:**
- Modify: `build-chimera-iso.sh`
- Create: `.github/workflows/chimera-docker-publish.yml`
- Create: `docs/docker-publishing.md`

**Interfaces:**
- `--push` or `CHIMERA_PUSH=1` publishes the built image.
- `DOCKER_REPOSITORY` overrides the default image repository.
- Credentials are supplied by `DOCKER_USERNAME` + `DOCKER_PASSWORD` or `DOCKER_ACCOUNT` + `DOCKER_ACCESS_TOKEN`.

- [ ] Test that local builds do not require Docker credentials.
- [ ] Add deterministic tags: configured tag, `latest`, and Git SHA when pushing.
- [ ] Authenticate using `--password-stdin`; never echo secrets.
- [ ] Add CI workflow using GitHub secrets and BuildKit/buildx.
- [ ] Document repository/secret setup.
- [ ] Run shell/workflow static validation and commit.

### Task 9: Verification

**Files:**
- Modify: existing CI validation workflow if required.
- Create: `tools/tests/test-aurora-runtime-integration.sh`

- [ ] Run `bash -n` on all modified shell scripts.
- [ ] Run all new shell tests.
- [ ] Validate asset manifests and symlinks.
- [ ] Build boot artifacts and verify required BIOS/UEFI files.
- [ ] Build ISO and run xorriso validation.
- [ ] Run Docker build without credentials and verify image exists locally.
- [ ] If credentials are available in CI, verify publish job configuration; do not fabricate a successful push.
- [ ] Commit final verification changes.
