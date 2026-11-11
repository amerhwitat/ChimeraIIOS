# Native Userspace Ecosystem — Implementation and Acceptance Plan

This roadmap defines the work needed to build a useful desktop userspace comparable in breadth to mainstream Windows, Linux, and macOS environments while preserving the native Koronos kernel and boot chain.

## Non-negotiable truthfulness rules
- A catalog entry is not an implementation. A successful host build is not a native target build.
- Browser previews, JavaFX tools, hosted services, compatibility layers, and emulator processes must be labeled honestly; none substitutes for a native kernel service.
- Never fabricate a userspace-ready marker, replace production ELFs with smoke probes, weaken the acceptance verifier, or call sequential CPU stepping genuine SMP.
- Keep production ISO and release publication fail-closed until the actual production payloads and all acceptance gates pass.
- Use upstream source repositories and license files. Preserve copyright notices, license texts, attribution, source-offer obligations, and modifications. Audit dependencies, bundled assets, trademarks, codec/patent considerations, and redistribution rights individually.

## Workstreams, in dependency order

### 1. Native execution foundation
1. Define the userspace ABI and stable syscall contract.
2. Complete ELF64 loading with segment bounds, BSS zero-fill, permission enforcement, NX/W^X, guarded user stacks, and failure rollback.
3. Bind each process to a scheduler-owned task/PID and process-owned page-table root.
4. Verify GDT/TSS/RSP0 and controlled CPL3 entry/return; preserve registers and validate syscall origin and arguments.
5. Implement correct yield, blocking, wake, exit, wait, and reap semantics. Unimplemented syscalls return explicit ENOSYS.
6. Add process isolation, mapping, malformed ELF, invalid-pointer, PID reuse, teardown, and concurrency regression tests.

### 2. Real production target payloads
1. Resolve the actual payload format: production initramfs artifacts are gzip-compressed while the current CPIO parser accepts uncompressed archives.
2. Implement bounded decompression with strict output-size, overflow, checksum, and timeout limits, or intentionally stage a supported uncompressed archive.
3. Replace shell-script /init entries with actual native ELF init/services, or add a real and tested script interpreter if script init is retained.
4. Produce distinct Live, Installer, and Recovery init binaries and stage them into the ISO through the canonical build.
5. Reject missing, malformed, ambiguous, wrong-target, or probe-only payloads explicitly.

### 3. Minimum usable native service stack
- VFS and file descriptors; path normalization, mount table, read/write/stat/readdir, EOF and error semantics.
- Process manager, IPC, wait/wake and service supervision.
- Device discovery and permission-checked device interfaces.
- Network stack and sockets, then DNS and TLS/certificate storage.
- Graphics, compositor/window management, input, fonts and clipboard.
- Audio, multimedia APIs, package lifecycle, logs, settings and power management.
Each service needs a versioned interface, explicit error behavior, unit tests, target integration tests and a health check. A service is RUNNING only after it actually starts and passes its health check.

### 4. Desktop shells and first-party applications
Retain Aurora Wayland Glass Desktop as the primary macOS-like shell and Marine Desktop as the Windows-like shell. Build a coherent launcher, task switching, settings, file manager, terminal, text editor, paint app, image viewer, PDF viewer, browser shell, media player, archive utility, calculator, screenshot tool, and package manager. Keep browser prototypes clearly labeled as prototypes until integrated into the actual target.

### 5. Upstream FOSS application ecosystem
Use docs/OPEN_SOURCE_USERSpace_CATALOG.json as a candidate catalog, not a support claim. Initial candidates include Firefox, LibreOffice, GIMP, Krita, Pinta, Inkscape, VLC, Audacity, Kdenlive, OBS Studio, Blender, FreeCAD, LibreCAD, 7-Zip, Calibre, KeePassXC, Geany, Git, SuperTuxKart, and DOSBox Staging.
These applications generally expect mature POSIX/Win32/Cocoa APIs, standard libraries, graphics/audio stacks and extensive dependencies. Do not claim they run natively until those dependencies exist and the application is ported and tested. For the near term, package only the projects that the supported runtime can genuinely execute; use hosted/browser versions only when clearly labeled and backed by the appropriate runtime.

### 6. Licensing and supply-chain gate
For every imported project, record upstream URL, exact commit/tag, SPDX license identifier(s), license-file hashes, copyright notices, dependency lockfile/SBOM, patches, build recipe, supported targets, known limitations, and test evidence. Do not bulk-copy code merely because it is publicly visible. Do not bundle proprietary firmware, ROMs, fonts, game assets, codecs or trademarks without verified rights.

### 7. Release acceptance
Run the canonical build, targeted tests, and then six independent actual-ISO boots: Live/Installer/Recovery × BIOS/UEFI. Keep the production verifier unchanged. Each case needs raw logs and artifact hashes proving a real target init ELF executed, made a CPL3-originated syscall, and completed a same-nonzero-PID readiness handshake. Separately prove Aurora startup, installation/reboot/installed boot, a real recovery operation, and AP-backed concurrent SMP.

## Status on creation
This document and catalog are planning/traceability inputs only. They do not claim that the listed applications have been imported, that native services are complete, or that production acceptance has passed. Release remains BLOCKED until evidence meets the gates above.


## Engineering update — 2026-10-20 (verified repository state)

The production bridge is still fail-closed and the release gate remains BLOCKED. The current OctavianOS bridge PR is [#93](https://github.com/amerhwitat/OctavianOS/pull/93); its source explicitly recognizes gzip magic and returns an unsupported-compression error because no bounded DEFLATE backend is present. Its own PR description confirms that the staged Live/Recovery initramfs files are gzip-compressed CPIO and that their current `/init` entries are shell scripts, not native ELF init services. The installer image is not proven to be a supported CPIO archive. A CPIO parser test that asserts gzip rejection is a correct negative test, not production payload support.

The related upstream production handoff gate is [ChimeraIIOS PR #162](https://github.com/amerhwitat/ChimeraIIOS/pull/162). The truthful-service-readiness work is tracked in [ChimeraIIOS PR #166](https://github.com/amerhwitat/ChimeraIIOS/pull/166) and [OctavianOS PR #91](https://github.com/amerhwitat/OctavianOS/pull/91). This ecosystem roadmap is [ChimeraIIOS PR #168](https://github.com/amerhwitat/ChimeraIIOS/pull/168) / [OctavianOS PR #94](https://github.com/amerhwitat/OctavianOS/pull/94). All are open, unmerged changes at the time of this update; this roadmap PR is documentation only.

### Required implementation order (do not skip gates)

1. Choose and enforce one real production payload contract. Preferred safe paths are either (a) make the canonical build stage a verified uncompressed `newc` CPIO for the native init path, with size limits and artifact validation, or (b) implement and fuzz-test a bounded gzip/DEFLATE decoder with strict output-size, header/trailer, checksum, and timeout/resource limits. Do not simply remove the gzip rejection or treat compressed bytes as CPIO.
2. Replace script-only production `/init` entries with target-specific, freestanding native ELF init programs. Define the required service startup/error contract and build dependencies; a smoke ELF must never substitute for these production binaries.
3. Wire the selected target ELF into scheduler-owned process/task state and a real PID; validate PT_LOAD/BSS, permissions, user stack, process page tables, GDT/TSS and ring-3 entry. Verify syscall entry originates at CPL3 and dispatches against the owning process.
4. Implement and test lifecycle/syscall backends in dependency order: GETPID/EXIT/EXIT_GROUP, MMAP/MUNMAP rollback, WAIT, bounded user-memory copy, and VFS/file I/O. Fail closed on unimplemented calls and do not fabricate PID or service readiness.
5. Build using the canonical repository builder and native Koronos build workflow; run unit/contract tests and preserve raw logs. The canonical local ISO command remains `./build-chimera-iso.sh --clean-state --storage-auto`; do not invent replacement flags or claim a build when no runner/log is available.
6. Run the unchanged verifier against six actual production ISO boots (Live, Installer, Recovery × BIOS, UEFI). Require a same nonzero scheduler-owned PID across target init, CPL3 syscall evidence, and readiness. Separately verify Aurora startup, installer transaction + reboot + installed boot, a real recovery repair operation, and AP-started concurrent SMP.

### Evidence ledger

- Production gzip payload extraction: **BLOCKED / not implemented**.
- Production-native Live/Installer/Recovery init ELFs: **BLOCKED / not established**.
- Scheduler-owned PID + production CPL3 syscall lifecycle: **NOT VERIFIED**.
- Canonical build from this update: **NOT RUN here**; no new build logs or ISO artifacts are claimed.
- Six-case production BIOS/UEFI matrix: **NOT PASSED / NOT VERIFIED**.
- Aurora, install/reboot, recovery repair, AP-backed SMP: **NOT VERIFIED**.
- Release publication: **KEEP BLOCKED**.

Update this ledger only when a corresponding code change, test output, and/or raw target boot artifact exists. CI checks for docs or routing probes must not be promoted into production acceptance evidence.
