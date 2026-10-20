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
