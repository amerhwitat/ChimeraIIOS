# Chimera II OS end-to-end acceptance gates

This checklist is the release gate for changes spanning the builder, Koronos, ISA catalog, Aurora, and imported userlands. A checklist item is **not passed** until a reproducible command or runtime artifact is attached to the release evidence.

## Required boot/build pipeline

Preserve this canonical order:

**Spit Fire → Jasper/GRUB → Koronos ELF → hardware/driver initialization → scheduler/runtime loop → live/recovery/installer userspace → Aurora**

- [ ] `bash -n build-chimera-iso.sh` succeeds.
- [ ] Build-stage resume order matches the actual stage loop.
- [ ] Docker-only and ISO-only routes are tested independently.
- [ ] Rootfs export uses a named, temporary container and validates the extracted rootfs before replacing the destination.
- [ ] ISO verification checks required BIOS/UEFI boot files, kernel ELF, initramfs/rootfs payload, installer/live/recovery entries, and checksums.
- [ ] Build logs, watchdog output, and failure-stage state are retained when a stage fails.
- [ ] A QEMU timeout or process exit is not counted as a successful boot without an explicit boot milestone.

## Capability evidence contract

Track each capability with a status and evidence record:

| Status | Minimum evidence |
| --- | --- |
| Discovered | Source URL, timestamp, matched term, and content hash where available |
| Cataloged | Schema-valid reviewed registry record |
| Implemented | Code reference plus focused tests |
| Compiled | Successful named build target and artifact hash |
| Booted | Runtime log or test output showing a defined boot milestone |
| Userspace-ready | Successful handoff and a demonstrated userspace operation |
| Conformance-tested | Named normative test suite, version, scope, and passing result |
| SMP-verified | At least two CPUs executing concurrently with per-CPU scheduler/context state and a concurrency test |

A candidate ISA, compiler output, successful ISO creation, or sequential multi-CPU simulation must not be promoted to stronger statuses.

## ISA and compatibility

- [ ] Validate the canonical ISA JSON and generated registry header deterministically.
- [ ] Keep encoding templates, exact sample encodings, and candidate metadata distinct; missing masks must not be counted as verified templates.
- [ ] For each implemented instruction, test decode, operand/immediate constraints, architectural state effects, exceptions, and encoder/decoder round trips where applicable.
- [ ] Record official conformance suite names, versions, test scope, and results. Never infer conformance from a catalog entry.
- [ ] Keep unimplemented architectures and Linux distribution/desktop profiles marked candidate/proposal-only until a pinned build, runtime test, licensing review, and hardware/runtime compatibility review pass.
- [ ] Do not let an RNN/LLM recommendation autonomously enable privileged code, drivers, or executable ISA support.

## Runtime services and safety

- [ ] Verify watchdogs for build stages and Koronos/microkernel/mobile runtime are separate, supervised, and tested for hung, exited, and healthy targets.
- [ ] Verify log rotation at the configured 1 GiB (`1,073,741,824` byte) per-file threshold, including concurrent writers, rotation failure, disk-full behavior, and retention cleanup. Do not claim a global log-directory cap unless separately enforced.
- [ ] Confirm discovery timers are enabled only where packaged, do not run on the compositor thread, and expose scan timestamp, errors, and candidate/review status in Aurora.
- [ ] Confirm SQL access from terminals/shells is explicit, permission-checked, and does not expose privileged database access to untrusted compatibility sessions.
- [ ] Confirm native and compatibility modes have distinct, documented syscall/ABI boundaries and regression tests.

## Evidence required for release

Attach the commit SHA, build command and environment, test commands and exit codes, ISO checksum, boot logs with named milestones, ISA validation output, and any failed/skipped tests. A missing artifact is **not verified**, not an implicit pass.

## Current limitation

This document defines acceptance criteria; it does not assert that every subsystem listed above is already implemented or that a full ISO build or hardware boot has passed.
