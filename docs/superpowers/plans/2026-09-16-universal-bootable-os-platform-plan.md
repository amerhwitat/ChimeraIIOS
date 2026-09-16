# Chimera II OS Universal Bootable Platform — Implementation Plan

**Design:** `docs/superpowers/specs/2026-09-16-universal-bootable-os-platform-design.md`
**Status:** Approved for implementation

## Phase 1 — Release foundation
- Add machine-readable release, filesystem, binary, package, driver and application integration registries.
- Add provenance/license fields and validation scripts.
- Add a release workflow that only publishes a GitHub Release after required build/test jobs pass.

## Phase 2 — Bootable ISO
- Expand the structured staging tree to contain `/src`, `/opt`, `/install`, `/drivers`, `/filesystems`, `/packages`, `/repositories`, `/man`, `/games`, `/wallets`.
- Preserve Spit Fire and Jasper source assets.
- Add Gates/Live/Install/Recovery/Diagnostics/Safe Graphics/Network boot menu entries.
- Add BIOS/El Torito and UEFI ESP validation and QEMU BIOS/UEFI smoke checks.
- Keep x86-64 as the first release target; keep ARM64/RISC-V64 metadata paths explicit until their native boot builders pass.

## Phase 3 — Installer
- Add hardware/firmware discovery manifest.
- Add transaction-oriented partition and filesystem planning.
- Add IPv4/IPv6 configuration schema and validation.
- Add Windows/Linux/macOS discovery/migration metadata without destructive defaults.

## Phase 4 — Compatibility/system integration
- Add driver registry and provenance workflow.
- Add filesystem capability registry.
- Add ELF/PE/COFF/Mach-O/WASM/Java/.NET/script registry.
- Add package-manager adapters and command/security reference registries.

## Phase 5 — Aurora/application integration
- Add manifest-driven integrations for `amerhwitat/nlp`, BizX, BizXtreme, general, Thamudic, games, networking, wallet tools and development/web stacks.
- Add Gates Menu category metadata.
- Build only applications whose declared source/license/dependencies can be verified by CI.

## Phase 6 — Mobile
- Preserve separate Mobile Microkernel architecture.
- Validate Android device profiles and hosted APK/AAB packaging paths.
- Add iOS/iPadOS metadata and non-destructive recovery/packaging helpers.

## Phase 7 — Release verification
- Generate ISO, hashes, manifest, SBOM/provenance metadata and source archive.
- Upload workflow artifacts.
- Publish GitHub Release only after validation succeeds.
- Update README with the actual release URL only after a real release exists.

## Verification gate
No implementation phase is considered complete from source edits alone. The corresponding CI job, artifact, checksum and test evidence must exist before the status is reported as complete.
