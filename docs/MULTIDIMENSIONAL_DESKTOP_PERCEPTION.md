# Multidimensional Desktop Perception Bridge

Status: **integration contract / research implementation plan**. This document does not claim live capture, trained-model accuracy, or release readiness until runtime checks pass.

## Scope

Use the existing Aurora Wayland backend, Aurora desktop assets, Marine desktop shell, and the existing multidimensional geometry/perspective layer. Keep the current 128D profile as a compatibility preset, not a hard maximum. Embedding dimension is a software tensor shape; it is not CPU register width, execution-lane count, or a claim about physical spacetime.

## Architecture and trust boundaries

1. **Frame provider (desktop-owned).** Aurora's compositor may provide a frame only after a per-session user grant. Marine uses the equivalent desktop-owned provider. Do not scrape display memory or expose DRM/KMS handles to the perception process.
2. **Capture broker.** Validate session, caller identity, permission, frame dimensions, pixel format, stride, buffer length and frame age. Revoke on lock screen, session end, permission withdrawal, or secure desktop.
3. **Isolated perception worker (unprivileged).** Receive read-only, bounded frame buffers through IPC/shared memory; no kernel pointers, arbitrary file access, input injection, or compositor control. Bound CPU/GPU time, memory, queue depth and model size. Drop stale frames instead of allowing unbounded queues.
4. **Vision adapters.** OpenCV can provide classical preprocessing/tracking; MediaPipe task models can provide configured detection/segmentation/landmarks; ONNX Runtime can run explicitly installed ONNX models. Model files are local, versioned, hash-checked deployment assets; never download or execute models implicitly.
5. **Multidimensional feature layer.** Emit named feature tensors with explicit dimension count, dtype, coordinate frame, normalization and model version. Support dimensions above 128 (including 256, 512, 1024 and 8192 test profiles) within an explicit memory budget. Reject zero, overflowed, or over-budget shapes.
6. **Result API.** Return typed detections, masks, tracks, OCR text and confidence with timestamps. Results are advisory data, never privileged commands. Desktop actions require a separate user-authorized action path.

## IPC contract (version 1)

Every request includes version, request_id, session_id, purpose, width, height, stride, pixel_format, timestamp_ns, payload_bytes, and a short-lived capability token. The broker validates that stride is at least width times bytes-per-pixel, multiplication does not overflow, and payload_bytes is at least stride times height; configured maximum frame bytes and dimensions are mandatory. Reject unknown versions, invalid tokens, stale timestamps, unsupported formats and truncated buffers.

Response includes version, request_id, status, model_id, model_sha256, processing_us, features and optional typed detections, segments, tracks and OCR. Never return raw frame pixels unless the requesting client separately has capture permission. Avoid logging pixels, OCR content, capability tokens or other sensitive payloads.

## Computer vision and model policy

- **Detection:** a locally installed model with documented labels, preprocessing, score threshold and NMS policy.
- **Segmentation:** a configured segmentation model; mask resolution and coordinate mapping are explicit.
- **Tracking:** stable per-session track IDs, timestamp-aware association, bounded lifetime, reset on scene/session changes.
- **OCR:** opt-in per application/window or explicit user action; do not persist recognized text by default.
- **Inference:** ONNX Runtime C/C++ is the default portable integration seam. CPU is the required baseline; GPU execution providers are optional and must gracefully fall back. Pin model hashes and record runtime/provider versions.
- No semantic accuracy claim until evaluated on a named, licensed dataset with precision/recall or task-appropriate metrics.

## Linux / Windows / Chimera boundary comparison

| Concern | Linux reference | Windows reference | Chimera / Octavian target |
|---|---|---|---|
| Display ownership | Wayland compositor; KMS is below user-space compositor | Desktop Window Manager and Windows Graphics Capture APIs | Aurora/Marine desktop-owned frame provider |
| Capture authorization | Portal-mediated user consent where supported; compositor policy | User-consent and OS capture APIs | Explicit per-session capability; deny by default |
| GPU/display control | DRM/KMS ioctls and driver interfaces | WDDM graphics stack and driver interfaces | HAL/display service; never expose device control to CV worker |
| Isolation | Process address spaces, credentials, namespaces/seccomp where available | User-mode process isolation, access tokens, restricted capabilities | Koronos process isolation/capability IPC as implemented; do not assume missing primitives exist |
| ML inference | User-space runtimes and vendor compute backends | User-space runtimes and DirectML/other supported backends | ONNX Runtime CPU baseline, optional provider plug-ins |
| Failure domain | Worker crash must not crash kernel/compositor | Worker crash must not crash kernel/DWM | Worker failure is contained; desktop continues without AI |

These are integration patterns, not a claim that Chimera already implements Linux/Windows-equivalent kernel facilities. Preserve POSIX-like APIs where feasible, but do not copy Linux kernel APIs into the Chimera kernel without an ABI and security review.

## Resource and privacy defaults

- Capture disabled until granted; visible indicator while capture is active.
- No capture on lock screen, secure prompts, credential entry, or excluded windows.
- Frame cap and queue depth are configurable; start with one in-flight frame and drop-oldest behavior.
- Bound model file size, tensor dimensions, allocations, runtime and response size.
- Do not persist frames, OCR, embeddings or tracking histories by default.
- Support immediate permission revocation and worker restart without desktop restart.
- Avoid automatic clicks, keystrokes, or other control based solely on model output.

## Acceptance tests (release gate)

1. Build the core with C++17, optimization, Wall, Wextra and pedantic flags; CI should treat warnings as failures.
2. Dimension tests: 1, 127, 128, 129, 256, 512, 1024 and 8192; check finite values, normalization, deterministic output and checked allocation.
3. Reject zero, overflow, truncated frames, invalid stride/pixel format, oversized dimensions, stale frame and invalid/revoked capability.
4. Fuzz image decoder and IPC parser; run address/undefined-behavior sanitizers where supported.
5. Test deterministic replay with fixed input/model/version; measure p50/p95 latency and peak RSS for representative 720p, 1080p and 4K frames.
6. Test consent denied, permission revoked, lock screen, app exclusion, worker crash and model missing/corrupt. The desktop must remain usable.
7. Model acceptance: dataset provenance/license, model SHA-256, per-task quality metrics, CPU-only fallback and resource budget.
8. Desktop acceptance: test Aurora and Marine on real compositor frame paths. A unit test or source-contract test is not evidence of live capture.

## Existing project assets and seams

- Chimera: desktop/aurora/wayland/aurora_wayland_backend.hpp, desktop/aurora/assets/aurora-desktop.svg, desktop/aurora/assets/aurora-wayland-glass.svg, tools/media/vision_mediapipe.py, multidimensional/.
- Octavian: use mirrored vendor/chimera-ii-os/source/ only as upstream source; keep the native Marine frame-provider adapter in Octavian's own desktop tree.
- Reuse existing Aurora/Marine artwork as UI branding only; wallpaper/image assets are not model weights and must not be treated as test evidence.

## Rollout gates

Phase 1: bounded parser, feature-vector tests and synthetic image fixtures.
Phase 2: optional local ONNX Runtime and task-model adapters.
Phase 3: broker IPC and mock frame provider.
Phase 4: compositor-backed capture and consent integration separately on Aurora and Marine.
Phase 5: performance/security tests and production evidence for each supported boot target.

Do not publish a release artifact until the model, capture, privacy, desktop-continuity and target-specific checks have passing evidence.
