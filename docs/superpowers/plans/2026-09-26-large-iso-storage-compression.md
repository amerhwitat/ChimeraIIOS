# Chimera II OS Large ISO, Storage Detection, and Compressed Runtime Payloads Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `build-chimera-iso.sh` so large ISO builds are storage-aware across Linux/Docker/WSL, can move build work to another drive when space is insufficient, compress runtime payloads and reference bundles, and boot/load a compressed kernel through a validated RAM-decompression path.

**Architecture:** Keep the existing source-first, checkpointed ISO pipeline and add focused storage, compression, manifest, and boot-artifact validation helpers rather than replacing the builder. Boot-critical files remain directly boot-readable; the kernel gets a small bootloader/decompressor path that validates and expands the compressed kernel into RAM. Non-boot-critical binaries use compressed-on-disk payloads with first-use decompression/cache, while the installer can materialize selected payloads.

**Tech Stack:** Bash, Docker/BuildKit, WSL2 detection, `df`/`findmnt`/`docker info`, SquashFS/xorriso/GRUB, zstd with gzip fallback where required, JSON manifests, SHA-256, existing Chimera boot contracts and CI.

**Spec:** The approved large-ISO/storage/compression design from the preceding conversation, extending the current repository's resumable ISO builder and existing QFS/source-first architecture.

## Global Constraints

- Preserve the existing resumable checkpoint/failure-state mechanism.
- Preserve BIOS/MBR and UEFI/GPT boot targets.
- Never silently erase, repartition, or overwrite an additional drive selected for build storage.
- Never execute downloaded SS64 web/reference content as code.
- Every compressed artifact must have size, algorithm, SHA-256, source/provenance, and load policy recorded.
- Boot-critical kernel/bootloader/initramfs artifacts must be validated before ISO mastering.
- A compressed kernel is decompressed into reserved RAM before kernel entry; firmware is not expected to execute a `.zst` object directly.
- Runtime compression must preserve executable mode and required metadata.
- CI must remain non-interactive and use deterministic temporary storage.
- Existing `--storage`, `--storage-auto`, `--no-storage-prompt`, `--resume`, `--clean-state`, `--docker-only`, and `--iso-only` semantics remain compatible.

## Review Focus

1. Docker Desktop/WSL VHDX has host free space but Docker's filesystem is full — storage diagnosis must report both rather than treating one as the other.
2. The preferred build drive fills after a checkpoint — the builder must pause/select another drive without discarding completed stages.
3. A compressed boot artifact is corrupt or missing — the build must fail before producing a bootable-looking but broken ISO.
4. A runtime binary is requested for execution — the decompressor/cache must validate and materialize it without changing its executable semantics.
5. SS64 content changes or is unavailable — the build must record provenance/failure clearly and never substitute unverified executable code.

---

### Task 1: Establish the compression and artifact contracts

**Files:**
- Create: `build/compression/chimera-compression.json`
- Create: `build/compression/compression-manifest.schema.json`
- Create: `build/compression/README.md`
- Test: `tests/build/test_compression_contract.py`

**Interfaces:**
- Produces the canonical artifact fields used by later build and boot stages: `path`, `source`, `algorithm`, `compressed_size`, `uncompressed_size`, `sha256`, `mode`, `load_policy`, and `boot_critical`.

- [ ] **Step 1: Write the failing contract tests**
  - Assert zstd is the preferred runtime algorithm.
  - Assert kernel artifacts use an explicit boot load policy.
  - Assert every artifact requires SHA-256 and both sizes.
  - Assert executable payloads record their mode.

- [ ] **Step 2: Run the tests to verify they fail**
  - Run: `python3 -m pytest tests/build/test_compression_contract.py -v`
  - Expected: FAIL because the contract files do not yet exist.

- [ ] **Step 3: Implement the JSON contract**
  - Define stable schema and version it independently from ISO version.
  - Define `runtime-cache`, `installer-materialize`, and `boot-ram` load policies.

- [ ] **Step 4: Run the tests**
  - Expected: PASS.

- [ ] **Step 5: Commit**
  - `git add build/compression tests/build/test_compression_contract.py`
  - `git commit -m "feat: define Chimera compression artifact contract"`

### Task 2: Extract storage detection into a testable helper

**Files:**
- Create: `tools/build/chimera-storage.sh`
- Modify: `build-chimera-iso.sh`
- Test: `tests/build/test_storage_detection.sh`

**Interfaces:**
- `chimera_is_wsl() -> status`
- `chimera_path_free_bytes PATH -> bytes`
- `chimera_detect_docker_root() -> path`
- `chimera_discover_storage_candidates() -> free_bytes|path records`
- `chimera_apply_storage_root PATH`
- `chimera_choose_larger_storage REASON REQUIRED_BYTES`

- [ ] **Step 1: Write shell tests for WSL, Docker-root, candidate-drive, and no-space cases.**
- [ ] **Step 2: Run tests and confirm failures.**
- [ ] **Step 3: Move/refactor the existing storage functions from `build-chimera-iso.sh` into the helper without changing current CLI behavior.**
- [ ] **Step 4: Add Docker Desktop VHDX and WSL distro VHDX reporting as diagnostics, explicitly distinguishing host free space from Docker filesystem free space.**
- [ ] **Step 5: Add deterministic non-interactive behavior: `--no-storage-prompt` fails with candidates and required/free numbers; `--storage-auto` chooses a sufficient candidate.**
- [ ] **Step 6: Run shell tests and a syntax check: `bash -n tools/build/chimera-storage.sh build-chimera-iso.sh`.**
- [ ] **Step 7: Commit.**
  - `git add tools/build/chimera-storage.sh build-chimera-iso.sh tests/build/test_storage_detection.sh`
  - `git commit -m "feat: make ISO storage detection Docker and WSL aware"`

### Task 3: Add large-ISO capacity planning and drive switching

**Files:**
- Modify: `build-chimera-iso.sh`
- Create: `build/storage/storage-policy.json`
- Test: `tests/build/test_large_iso_storage.sh`

**Interfaces:**
- `calculate_required_storage_bytes() -> bytes`
- `ensure_storage_capacity STAGE REQUIRED_BYTES`
- `write_storage_report PATH`

- [ ] **Step 1: Write tests for required-space calculation, reserve space, and drive switch while preserving the checkpoint file.**
- [ ] **Step 2: Run tests and confirm failure.**
- [ ] **Step 3: Implement capacity estimates using current rootfs/source size plus SquashFS expansion, ISO reserve, Docker working reserve, and configured safety margin.**
- [ ] **Step 4: Call capacity checks before Docker, rootfs, SquashFS, and ISO mastering stages.**
- [ ] **Step 5: On insufficient capacity, offer an explicit path or detected drive; create the build/output directories there and keep the existing state/checkpoints accessible.**
- [ ] **Step 6: Add `--large-iso`/environment configuration while retaining current large-ISO default behavior.**
- [ ] **Step 7: Generate `ISO/storage-report.json` with detected filesystems, required bytes, selected root, Docker root, and decision history.**
- [ ] **Step 8: Run tests and a dry-run storage report.**
- [ ] **Step 9: Commit.**

### Task 4: Implement deterministic runtime payload compression

**Files:**
- Create: `tools/runtime/chimera-compress-payloads.sh`
- Create: `tools/runtime/chimera-runtime-loader.sh`
- Create: `tests/runtime/test_payload_compression.sh`
- Modify: `build-chimera-iso.sh`

**Interfaces:**
- `chimera_compress_file INPUT OUTPUT MANIFEST`
- `chimera_verify_compressed_file INPUT COMPRESSED MANIFEST`
- `chimera_materialize_runtime_payload ID DESTINATION`

- [ ] **Step 1: Write tests using a small executable fixture and assert compressed output, SHA-256, mode, and round-trip equality.**
- [ ] **Step 2: Run tests and confirm failure.**
- [ ] **Step 3: Implement zstd compression with an explicit fallback policy for environments without zstd.**
- [ ] **Step 4: Implement first-use decompression into a controlled runtime cache, verify SHA-256 before execution, and preserve mode.**
- [ ] **Step 5: Add cache cleanup hooks based on configured size/age rather than deleting arbitrary files.**
- [ ] **Step 6: Integrate the compression stage after binaries are compiled/staged and before SquashFS creation.**
- [ ] **Step 7: Verify every compressed payload by decompression test before it enters the ISO.**
- [ ] **Step 8: Commit.**

### Task 5: Add compressed kernel packaging and boot handoff contract

**Files:**
- Create: `boot/kernel/chimera-kernel-loader.c`
- Create: `boot/kernel/chimera-kernel-format.h`
- Create: `boot/kernel/kernel-compression.json`
- Create: `tests/boot/test_kernel_compression.py`
- Modify: existing boot build/staging files identified by repository search
- Modify: `build-chimera-iso.sh`

**Interfaces:**
- Kernel package header contains magic, version, compression algorithm, compressed/uncompressed sizes, load address/constraints, entry address, and SHA-256 metadata.
- Loader interface: `chimera_load_compressed_kernel(package, reserved_ram, size) -> kernel_entry`.

- [ ] **Step 1: Write format/validation tests for valid, truncated, wrong-hash, and unsupported-algorithm packages.**
- [ ] **Step 2: Run tests and confirm failure.**
- [ ] **Step 3: Define a small architecture-neutral package header and architecture-specific handoff hooks; do not invent x86 real-mode behavior for non-x86 targets.**
- [ ] **Step 4: Implement the loader/decompressor boundary used by the boot environment.**
- [ ] **Step 5: Package the kernel as compressed plus validated metadata, while retaining an uncompressed recovery/debug artifact in the build output.**
- [ ] **Step 6: Add boot staging checks ensuring Spit Fire/Jasper can locate the package and the loader before ISO mastering.**
- [ ] **Step 7: Run unit tests and static compilation checks for the loader.**
- [ ] **Step 8: Commit.**

### Task 6: Integrate SS64 reference acquisition and compression

**Files:**
- Create: `docs/ss64/ss64-sources.json`
- Create: `tools/docs/fetch-ss64-references.sh`
- Create: `tests/docs/test_ss64_bundle.sh`
- Modify: `build-chimera-iso.sh`

**Interfaces:**
- `fetch_ss64_references OUTPUT_DIR MANIFEST`
- Produces compressed documentation only; never produces an executable binary from SS64 pages.

- [ ] **Step 1: Write tests for provenance fields, offline failure behavior, archive integrity, and separation from executable payload directories.**
- [ ] **Step 2: Run tests and confirm failure.**
- [ ] **Step 3: Implement an allowlisted source catalog with URL, retrieval date, license/terms note, and SHA-256.**
- [ ] **Step 4: Download only the documented/reference material that is permitted by the source terms; fail clearly if retrieval is unavailable rather than silently substituting another source.**
- [ ] **Step 5: Compress the reference bundle and generate its manifest.**
- [ ] **Step 6: Stage it under `/man/ss64` and integrate it with the existing `/man` source-first layout.**
- [ ] **Step 7: Run tests and commit.**

### Task 7: Make the ISO builder enforce artifact completeness

**Files:**
- Create: `tools/build/chimera-artifact-verify.sh`
- Create: `tests/build/test_iso_artifacts.sh`
- Modify: `build-chimera-iso.sh`

**Interfaces:**
- `chimera_verify_boot_artifacts ISO_TREE MANIFEST`
- `chimera_verify_runtime_artifacts ISO_TREE MANIFEST`
- `chimera_verify_compressed_artifact ARTIFACT MANIFEST`

- [ ] **Step 1: Write tests reproducing the previous missing `chimera-live-initramfs.img` / `live-manifest.json` class of failure.**
- [ ] **Step 2: Run tests and confirm failure.**
- [ ] **Step 3: Verify all boot-critical paths, JSON contracts, kernel/initramfs, GRUB assets, Spit Fire/Jasper artifacts, and compressed manifests before xorriso.**
- [ ] **Step 4: Verify every compressed artifact can be decompressed and hash-checked.**
- [ ] **Step 5: Make the ISO stage refuse to run if verification fails.**
- [ ] **Step 6: Commit.**

### Task 8: Integrate CI and documentation

**Files:**
- Modify: `.github/workflows/chimera-iso.yml`
- Modify: `.github/workflows/chimera-release.yml`
- Modify: `README.md`
- Modify: `BUILD_SYSTEM_COMPLETE.md`
- Modify: `COMPLETE_BUILD_GUIDE.md`
- Create: `docs/LARGE_ISO_BUILD.md`

- [ ] **Step 1: Add CI tests for compression manifests, artifact validation, and non-interactive storage handling.**
- [ ] **Step 2: Ensure CI does not wait for interactive drive selection.**
- [ ] **Step 3: Document local Windows/WSL, native Linux, Docker Desktop, and CI storage behavior.**
- [ ] **Step 4: Document compressed-kernel boot flow and runtime decompression/cache policy.**
- [ ] **Step 5: Document SS64 provenance and the fact that reference pages are not executable code.**
- [ ] **Step 6: Commit.**

### Task 9: Full verification and integration review

**Files:**
- No new production files; verify all files from Tasks 1-8.

- [ ] **Step 1: Run shell syntax checks across all modified `.sh` files.**
- [ ] **Step 2: Run Python contract tests.**
- [ ] **Step 3: Run runtime compression round-trip tests.**
- [ ] **Step 4: Run boot package/loader tests.**
- [ ] **Step 5: Run artifact validation against a representative staged ISO tree.**
- [ ] **Step 6: Run the builder in non-destructive dry-run/storage-diagnostic mode.**
- [ ] **Step 7: Run a real ISO build when the environment has sufficient disk space and required build dependencies.**
- [ ] **Step 8: Inspect ISO contents and boot metadata; do not claim successful boot until the available QEMU/firmware smoke tests actually pass.**
- [ ] **Step 9: Run the repository's existing CI/test suite and resolve regressions.**
- [ ] **Step 10: Commit the integrated implementation with a final verification summary.**

## Expected Result

The resulting builder will dynamically understand the distinction between repository, Linux, Docker, WSL host, and WSL VHDX storage; use a large-build storage root when necessary; preserve resumable checkpoints when storage moves; build a large bootable ISO; compress runtime binaries and SS64 reference material; package and validate a compressed kernel that is expanded into RAM before kernel entry; and refuse to produce an ISO when any boot-critical artifact or compressed payload is missing/corrupt.
