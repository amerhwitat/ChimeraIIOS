# Chimera II Web / Repository Audit — 2026-10-07

## Scope
Audited the GitHub repository, GitHub Pages deployment boundary, Aurora web entrypoints, PlayStation Hub integration, and GitHub Actions configuration.

The public Pages endpoint could not be directly fetched from this execution environment, so deployed-site behavior was cross-checked against the repository's Pages bundle and deployment workflow.

## Fixed findings
- GitHub Pages deployment now publishes only web/, not the entire repository.
- Removed duplicate pages.yml deployment workflow so Pages has one canonical deployment path.
- Removed the obsolete self-removing Docker-log repair workflow.
- Fixed hypervisor Docker image tags when Docker Hub credentials are absent; local fallback tags are now valid.
- Removed the PHP PlayStation detection endpoint because GitHub Pages is static and cannot execute PHP.
- PlayStation Hub now uses a static-safe local-bridge status boundary.
- Added the PlayStation Hub to the Aurora Control Center navigation and overview.
- Extended web integrity CI to validate the PlayStation manifest, UI assets, JavaScript syntax, and absence of the obsolete PHP endpoint.
- Repaired a corrupted Koronos workflow step that contained literal \\n sequences instead of YAML newlines.
- Consolidated Pages deployment responsibilities so build/release validation and Pages deployment are not competing deployment implementations.

## Runtime boundary
GitHub Pages remains a static catalog/UI surface. Native emulator binaries, ROMs, BIOS images, proprietary firmware, and local launch operations remain on the Chimera II/Aurora machine.

## Verification
Repository paths for the repaired Pages and PlayStation surfaces were rechecked after the changes. New GitHub Actions runs were observed for the updated commit. GitHub Actions was heavily queued during the audit; immediate failures with zero reported jobs were treated as runner/workflow-startup failures rather than falsely attributed to application code.

## Remaining environment-dependent verification
A full local ISO boot, native emulator execution, GPU/Wayland behavior, and the exact deployed Pages response require a real Chimera II host or a completed GitHub Actions build/deployment run. This environment cannot truthfully claim those hardware/runtime tests passed.
