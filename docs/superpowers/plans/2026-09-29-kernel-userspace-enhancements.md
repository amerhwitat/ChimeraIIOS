# Chimera II Kernel + User Space Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend Chimera II OS kernel and user space into a coherent, testable platform for Koronos parallel services, native desktop operation, Windows/NT compatibility, PE execution, graphics/input, security, storage, networking, diagnostics, and recovery without destabilizing the existing boot path.

**Architecture:** Keep Koronos as the kernel scheduler/IPC/interrupt/runtime foundation and Kore as the service/object-management layer. Build user-space capabilities as independent services with explicit dependencies and health states; Windows compatibility remains an ABI/runtime layer over native Chimera services rather than a second kernel. Implement each subsystem incrementally with host-side tests before ISO integration.

**Tech Stack:** C/C++20, C11, x86-64 boot/runtime, ASM, CMake, existing Koronos/Kore/Aurora architecture, Python for build/inspection tooling, JSON service/compatibility manifests.

**Spec:** `docs/superpowers/plans/2026-09-29-kernel-userspace-enhancements.md` plus the approved Windows/NT desktop compatibility design from the preceding conversation.

## Global Constraints

- Preserve the existing Koronos boot handoff and Multiboot2 module ABI.
- Do not replace Koronos with a second scheduler; Windows-compatible threads map onto the native scheduler.
- Keep kernel code freestanding where required; user-space code must not introduce kernel-only dependencies.
- Windows compatibility implementations must be original/clean-room compatible interfaces; do not copy proprietary Windows implementation or confidential source.
- PE loading must validate architecture, bounds, sections, relocations, imports, exports, TLS and entry-point state before execution.
- No claim of successful ISO/runtime execution until the corresponding local or CI verification actually passes.
- Every service target must expose explicit state, dependencies, startup diagnostics and failure behavior.
- Build scripts must remain resumable and must not silently execute documentation/code examples embedded in heredocs.

## Review Focus

- Scheduler starvation/re-entrancy and persistent READY/RUNNING/BLOCKED/EXITED lifecycle — covered by scheduler stress tests.
- Malformed/cross-architecture PE files and unsafe import/relocation data — covered by PE loader negative tests.
- GUI message storms and blocked UI threads — covered by message-queue and wait/wake tests.
- Parallel service dependency cycles/failures — covered by target-graph tests.
- Boot/ISO regression after adding services — covered by ELF, manifest, ISO-content and boot-contract verification.

---

### Task 1: Kernel scheduler and thread foundation

**Files:**
- Modify: `kernel/core/scheduler.cpp`
- Modify: `kernel/core/scheduler.h` or the existing scheduler header path discovered from the repository
- Create: `kernel/core/thread.cpp`
- Create: `kernel/include/chimera/thread.h` when no existing equivalent exists
- Test: `tests/kernel/scheduler_*` or the repository's existing kernel-test location

**Interfaces:**
- Produces persistent task states `READY`, `RUNNING`, `BLOCKED`, `EXITED`.
- Produces `chimera_sched_yield`, block/wake, task snapshots, CPU affinity and per-thread execution counters.
- Produces thread creation/exit/current-thread primitives used by NT compatibility.

- [ ] Write scheduler lifecycle tests covering repeated execution, block/wake, exit, priority and multiple CPUs.
- [ ] Run the tests and confirm failures for missing lifecycle behavior.
- [ ] Implement the minimum lifecycle/thread primitives over the existing scheduler.
- [ ] Run the scheduler tests and sanitizer/host checks.
- [ ] Commit the kernel scheduler/thread milestone.

### Task 2: Kernel synchronization, waits, timers, APC/DPC

**Files:**
- Create/modify: `kernel/core/sync*`, `kernel/core/timer*`, `kernel/core/apc*`, `kernel/core/dpc*` according to existing repository conventions
- Create/modify: corresponding `kernel/include/chimera/*` headers
- Test: synchronization and wait tests

**Interfaces:**
- Events, mutexes, semaphores, wait sets, timers, alertable waits, APC queues and deferred kernel work.

- [ ] Add failing tests for event/mutex/semaphore semantics and wait wakeups.
- [ ] Implement synchronization objects using Koronos scheduler blocking/wakeup.
- [ ] Add timer and deferred-work queues.
- [ ] Add APC/DPC dispatch tests and verify no busy-spin behavior.
- [ ] Commit the synchronization milestone.

### Task 3: NT object/process/handle/security foundation

**Files:**
- Create: `kernel/compat/nt/object*`, `process*`, `handle*`, `token*` or the repository's established NT compatibility paths
- Modify: compatibility CMake manifests
- Test: object/handle/process/security tests

**Interfaces:**
- Object headers, reference counts, handles, process/thread objects, tokens, SID/ACL/security descriptor primitives and job objects.

- [ ] Define failing tests for handle lifetime, duplicate/close, process/thread objects and access checks.
- [ ] Implement the object manager and handle table.
- [ ] Implement process/thread/security-token foundations.
- [ ] Run lifecycle and negative-security tests.
- [ ] Commit the NT foundation milestone.

### Task 4: Parallel target/service manager integration

**Files:**
- Modify: existing Kore/systemd-style service manager files
- Create/modify: `system/services/targets/*.json` and service manifests
- Modify: boot/runtime startup path
- Test: target graph and dependency tests

**Interfaces:**
- Targets for `hardware`, `storage`, `network`, `security`, `nt-compat`, `win32`, `graphics`, `desktop`, `installer`, `live` and `complete-system`.
- Dependency ordering, parallel startup, health state, restart policy and diagnostic logging.

- [ ] Write graph tests including parallel branches and dependency cycles.
- [ ] Implement deterministic dependency resolution and parallel launch.
- [ ] Add service health/error propagation without stalling unrelated targets.
- [ ] Integrate boot diagnostics and runtime progress reporting.
- [ ] Commit the service-target milestone.

### Task 5: Win32 message/input/window foundation

**Files:**
- Create/modify: `compat/windows/user32/*`
- Create/modify: `compat/windows/include/*`
- Test: message queue/window tests

**Interfaces:**
- `HWND`, window classes, window procedures, per-thread message queues, `GetMessage`, `PeekMessage`, `TranslateMessage`, `DispatchMessage`, `PostMessage`, `SendMessage`, timers, keyboard/mouse input and focus/capture.

- [ ] Write tests for message ordering, thread ownership, queue wakeups and nested dispatch.
- [ ] Implement per-thread queues integrated with scheduler waits.
- [ ] Implement window object hierarchy and dispatch.
- [ ] Implement input translation and focus/capture.
- [ ] Commit the USER/message milestone.

### Task 6: GDI/graphics/compositor foundation

**Files:**
- Create/modify: `compat/windows/gdi32/*`
- Modify: `desktop/aurora/*` and graphics HAL integration points
- Test: GDI object and raster tests

**Interfaces:**
- DCs, bitmaps, fonts, brushes, pens, regions, basic raster/text operations and presentation surfaces.

- [ ] Add failing tests for GDI object lifetime and basic raster operations.
- [ ] Implement object handles and drawing primitives.
- [ ] Connect presentation to the existing Aurora compositor without bypassing native graphics services.
- [ ] Test multi-window rendering and resize/occlusion behavior.
- [ ] Commit the graphics milestone.

### Task 7: PE executable/DLL runtime completion

**Files:**
- Modify: `compat/windows/pe/pe_loader.cpp`
- Create/modify: import resolver, API-set resolver, process launcher, TLS/unwind support
- Modify: `tools/runtime/chimera-pe.py`
- Test: PE fixture suite

**Interfaces:**
- PE32/PE32+ mapping, relocations, import/IAT binding, exports, TLS, architecture checks, DLL dependency loading and EXE entry-point launch.

- [ ] Add malformed-PE, missing-import, relocation and architecture-mismatch tests.
- [ ] Implement dependency resolution and IAT binding against Chimera providers.
- [ ] Implement DLL load/unload lifecycle and EXE process creation.
- [ ] Integrate TLS and exception/unwind registration where the native execution architecture supports it.
- [ ] Verify with small known-safe PE fixtures before attempting desktop applications.
- [ ] Commit the PE runtime milestone.

### Task 8: KERNEL32/ADVAPI32/SHELL32/WS2_32 compatibility surfaces

**Files:**
- Create/modify: `compat/windows/kernel32/*`
- Create/modify: `compat/windows/advapi32/*`
- Create/modify: `compat/windows/shell32/*`
- Create/modify: `compat/windows/ws2_32/*`
- Test: API behavior tests

**Interfaces:**
- Process/thread/memory/file APIs, synchronization, registry/service APIs, shell notifications and Winsock mapping.

- [ ] Define tests for each API family against native Chimera backing services.
- [ ] Implement the compatibility shims without duplicating kernel logic.
- [ ] Add shell-change notification delivery through the event/message system.
- [ ] Integrate Winsock compatibility with Spotnik.
- [ ] Commit the core Win32 API milestone.

### Task 9: Desktop shell and Windows-style features

**Files:**
- Modify/create: `desktop/aurora/shell/*`
- Modify/create: taskbar, launcher, notification, virtual-desktop, file-manager and settings services
- Test: desktop service tests and UI smoke tests

**Interfaces:**
- Taskbar, launcher/Start, Alt+Tab, virtual desktops, snap layouts/groups, notifications, clipboard, drag/drop, search, file manager, settings, display/DPI and multi-monitor abstractions.

- [ ] Add service-level tests for each desktop manager state machine.
- [ ] Implement window-switching, snap and virtual-desktop state.
- [ ] Implement shell services over USER32/GDI and native compositor.
- [ ] Integrate file search/indexing and clipboard services.
- [ ] Run desktop smoke tests under the host graphical test environment where available.
- [ ] Commit the desktop milestone.

### Task 10: Storage, networking, device and multimedia user-space enhancements

**Files:**
- Modify: existing VFS/storage services
- Modify: Spotnik/network compatibility
- Create/modify: multimedia and device service manifests
- Test: service/API tests

**Interfaces:**
- Unified file I/O, async I/O/IOCP, named pipes, sockets, display/audio device abstractions and hardware discovery.

- [ ] Add asynchronous I/O and completion tests.
- [ ] Integrate device discovery with service targets.
- [ ] Add multimedia service interfaces without coupling applications directly to drivers.
- [ ] Verify network/storage services can restart independently.
- [ ] Commit the I/O/device milestone.

### Task 11: Security, recovery and diagnostics

**Files:**
- Modify: existing Secure Boot/TPM/security services
- Create/modify: code-integrity, audit, diagnostics and recovery services
- Test: policy and failure-injection tests

**Interfaces:**
- Boot measurement, module validation, permissions, audit events, crash diagnostics, safe mode/recovery target and service isolation.

- [ ] Write policy and failure-injection tests.
- [ ] Integrate security checks with PE loading and driver/module loading.
- [ ] Add recovery/safe-mode target and structured boot logs.
- [ ] Verify failed desktop/user services do not compromise kernel boot.
- [ ] Commit the security/recovery milestone.

### Task 12: Build/ISO integration and compatibility test matrix

**Files:**
- Modify: `build-chimera-iso.sh`
- Modify: CMake manifests and install manifests
- Create: `tests/compatibility/` fixtures and test runner
- Modify: CI workflows

**Interfaces:**
- Reproducible host build, staged runtime assets, bootable ISO, installer/live target manifests and automated verification.

- [ ] Add tests that assert every declared runtime binary exists in the ISO staging tree.
- [ ] Add PE/Win32 compatibility fixture tests to CI.
- [ ] Add service graph, boot log, Multiboot2 and installer initialization checks.
- [ ] Make the build script print progress for every stage and fail with actionable diagnostics.
- [ ] Build a clean ISO from an empty build directory.
- [ ] Run final verification of ELF, ISO contents, service manifests and compatibility fixtures.
- [ ] Commit the integration milestone and document exact verification commands/results.

## Final Verification

- [ ] Host unit tests pass.
- [ ] PE negative/positive fixtures pass.
- [ ] CMake configure/build succeeds from a clean directory.
- [ ] Koronos ELF64 verification succeeds.
- [ ] Multiboot2 module registry verification succeeds.
- [ ] Service target graph has no dependency cycles.
- [ ] Installer and Live targets reach their initialization state without scheduler stalls.
- [ ] ISO staging contains every declared runtime binary and manifest.
- [ ] VMware/QEMU boot smoke test reaches Koronos runtime and Aurora/installer target selection.
- [ ] No completion claim is made until the corresponding command output is observed.
