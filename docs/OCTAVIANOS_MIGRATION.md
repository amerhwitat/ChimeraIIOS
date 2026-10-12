# OctavianOS Repository and Codebase Migration

**Status:** Phase 0 identity marker committed; repository creation/rename and repository-wide migration remain incomplete.

## Target identity

- Product / OS name: **OctavianOS**
- Target GitHub repository: `amerhwitat/OctavianOS` (not yet created)
- Legacy source repository: `amerhwitat/ChimeraIIOS`
- Legacy names are retained only where required for source compatibility, historical provenance, ABI symbols, migration aliases, and backward-compatible paths. New user-facing branding must say OctavianOS.

## Migration goals

Create a new OctavianOS repository from the complete, history-preserving Chimera II OS source tree, then reorganize it into explicit layers without silently dropping existing work:

1. **Boot chain:** Spit Fire → Jasper/GRUB → Koronos ELF → hardware/driver initialization → scheduler/runtime loop → live/recovery/installer userspace → Aurora.
2. **Kernel and architecture:** Koronos, microkernel interfaces, memory management, ELF loading, scheduling, drivers, interrupts, SMP, platform/firmware abstraction.
3. **ISA and execution:** version-pinned source imports, encoding/decoding, architectural state, interpreter/JIT or translator backends, native Chimera N-bit model, compatibility layers and conformance evidence.
4. **Userspace and desktop:** live environment, installer, recovery, diagnostics, services, command shells, SQL runtime, Aurora desktop and applications.
5. **Build and distribution:** reproducible toolchains, ISO/USB builders, hosted/mobile editions, container images, package manifests, SBOM/license records and release artifacts.
6. **Validation:** unit/contract tests, architecture-specific ISA tests, emulator boot tests, ISO-content checks, runtime userspace acceptance tests and hardware qualification.

## Repository creation and migration procedure

1. Freeze a source commit and record its SHA, branch inventory, submodule/LFS state, licenses and artifact provenance.
2. Create `amerhwitat/OctavianOS` as a public repository, preserving the source repository's GPL-3.0 license and relevant notices.
3. Transfer the complete Git history and refs, including relevant branches and tags. Do not reconstruct the project from a shallow list of files or copy only the default branch.
4. Add a migration manifest mapping old paths and names to the new layout; keep compatibility shims where paths or ABI identifiers are externally consumed.
5. Rename user-visible labels, desktop/boot artwork metadata, installer screens, package/app IDs, Docker tags, ISO labels, documentation, workflow titles, scripts, tests and release metadata in small, reviewable batches.
6. Update URLs and cross-repository references only after the target repository exists; add a migration notice and preserve redirects from the old GitHub URL if the repository is renamed rather than copied.
7. Run static reference searches and build/test workflows from the new default branch. Build the full ISO from the exact merged commit and publish artifact hashes.
8. Retain the legacy repository until the new repository passes the acceptance gates and the migration has been reviewed.

## Required boot/runtime acceptance gates

Configuration parsing is not a runtime handoff. A successful kernel compile is not userspace readiness. Before calling the boot path complete:

- Locate a real, built installer userspace ELF and recovery userspace/initramfs in the staged ISO; verify manifests, hashes, architecture, ELF machine, load segments and entry point.
- Implement a memory-safe loader and a defined privilege/address-space transition. Do not jump to an ELF entry point until segment mapping, BSS zeroing, permissions, stack/ABI, argument/environment handoff and fault handling are implemented.
- Launch the installer userspace from the installer menu and capture an observable ready marker over QEMU serial/debug console.
- Launch recovery userspace for diagnostics mode, demonstrate a working recovery console or diagnostics service, and test malformed/missing payload failure paths.
- Exercise each Jasper/GRUB target in QEMU; verify the x86_64 ISO refuses ARM64/mobile execution and directs users to an architecture-specific image.
- Build and inspect the final ISO, assert all required boot assets are present, and retain QEMU traces and artifact SHA-256 values.

## ISA import and implementation gates

- Pin official machine-readable sources to revisions/releases and preserve source URL, version, extension, licensing, import timestamp and original encoding definitions.
- Keep instruction *forms* separate from mnemonic families; model prefixes, opcode maps, operand encodings, immediate widths, extension requirements, reserved/illegal encodings and architecture revision.
- Import and validate source data before adding derived effects. Do not infer register/flag/memory effects solely from mnemonic names when an authoritative instruction description is available.
- Mark each form independently as documented, cataloged, encoded, decoded, executed, differential-tested and conformance-tested. An architecture identifier or candidate row is not complete ISA coverage.
- Use a shared typed intermediate representation only as a lowering boundary. Preserve guest architectural state, memory ordering, privilege, traps, flags, MMU/PMP, interrupts, floating-point/vector behavior and ABI semantics.
- Gate each native, compatibility and Chimera N-bit execution path separately. Recommendations and metadata are not executable backends.
- Add official architecture suites and differential tests before marking conformance; report unsupported revisions and extension gaps explicitly.

## Reorganization principles

- Prefer source-first and reproducible builds; avoid committing generated binaries unless they are release artifacts with provenance.
- Keep freestanding kernel code separate from hosted utilities and GUI code.
- Separate architecture-neutral interfaces from architecture-specific implementations.
- Preserve current Aurora artwork and asset contracts; do not reintroduce the obsolete `aurora-background.jpg` contract.
- Keep ARM64/mobile support separate from the x86_64 ISO unless a target-specific boot image and runtime path are actually built and tested.
- Maintain a capability/evidence matrix so documented, cataloged, compiled, booted, userspace-ready and conformance-tested are never conflated.

## Current blockers

- The available GitHub connection can create branches, commits and pull requests in the existing repository, but does not expose the GitHub repository-creation or repository-rename administration operation. Therefore `amerhwitat/OctavianOS` has **not** been created by this workflow.
- The local checkout at `/mnt/c/tmp/ChimeraIIOS` is not mounted in this execution environment, so a complete local clone, source-wide refactor and full local build cannot be claimed.
- The existing boot-routing PR still does not prove that installer and recovery userspace actually execute.
- The ISA candidate inventory is not yet exhaustive; the current report covers 104 architecture identifiers, with 15 containing some catalog rows and 89 lacking instruction rows.

This document is a migration contract and checklist, not evidence that any listed implementation or acceptance gate has passed.
