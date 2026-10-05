# Local ROM inventory, MAME detection, and Aurora integration

Status: proposed design for review  
Repository: `amerhwitat/ChimeraIIOS`  
Target base: `main`

## Goal

Make locally installed ROMs and emulator binaries discoverable from Aurora, prefer MAME when the installed MAME build confirms that it supports the selected system and media, and use a checked compatible emulator only when MAME cannot identify or mount that media. Keep the user's ROMs, BIOS images, and unverified emulator archives on the user's machine.

The inspected collection contains 10,250 files (about 6.24 GB), primarily TAP, ADF, ST, CRT, MSA, and ROM files. It includes proprietary and uncertain-provenance content, so repository changes must contain only generic code and metadata schemas.

## Current repository contracts to preserve

- `emulation/retro_systems.json` already describes system families, candidate backends, and distribution restrictions.
- `config/aurora/emulators.json`, `config/aurora/emulator-associations.json`, and `aurora/emulators/launch-retro.sh` provide emulator definitions and launch mappings.
- The Aurora emulation panel currently exposes the Sakhr registry rather than the complete retro-system catalog.
- `tools/chimera-rom-search.sh` and `config/aurora/rom-search.json` support discovery but do not download ROMs.
- Existing policy requires user-provisioned ROMs, BIOS, licenses, and hashes. Keep these safeguards.
- `desktop/aurora/aurora-session.sh` runs during login. It must not scan the ROM tree, hash media, query every MAME driver, or build emulator indexes on the critical desktop-start path.

## Proposed behavior

### Local catalog

Add a local-only inventory command that recursively indexes user-selected ROM and BIOS roots. The default ROM root is `~/Games/ROMs`; BIOS remains `~/Games/BIOS`. Allow alternate roots, including the already authorized Windows source path during local use, without hard-coding that path into the repository.

Store the catalog beside the user's data, for example `~/.local/share/chimera/media-index.json`. Record relative path, filename, size, extension, SHA-256, detected format/system hints, scan time, and rights/provenance state (`unverified` unless the user supplies a verified declaration). Do not store absolute source paths in a portable export. Skip symlink escapes, report unreadable files, and never extract nested archives. Refresh on explicit request or a background maintenance action, not during boot or login.

The tool may inspect emulator executable paths and versions, but must not execute binaries found inside ROM folders or unverified archives. Accept emulator executables only from configured/trusted install locations or an explicit user-selected path; identify the binary and version in the local catalog.

### MAME capability discovery and launch

At setup or an explicit refresh, query the configured MAME binary for its version and supported systems. Query media support per selected system/driver rather than assuming that an extension maps to one universal machine. Use MAME's machine and software-list metadata to identify candidates and verify expected media where available. Cache capability results against MAME's resolved path, version, and metadata fingerprint; invalidate the cache when these change.

For a launch request:

1. Resolve the selected file to a candidate system using catalog metadata and user choice where ambiguous.
2. Ask the selected MAME build whether that system and media type are supported.
3. Launch MAME when the support check succeeds and the file passes required path, hash, and license/provenance policy.
4. If MAME cannot identify or mount the media, offer only a checked fallback whose configured system mapping and extension/media compatibility both match. Show the selected backend and reason in the panel.
5. If there is no checked backend, explain the missing system/media capability and provide a way to choose another installed emulator. Never silently relabel unsupported media as supported.

Use the existing emulator registry and Aurora window/launch bridge. Extend the panel to show all catalogued systems, installed backends, compatible media counts, and unsupported/ambiguous items. Do not treat a filename extension alone as proof of compatibility.

MAME's documented `-version`, `-listfull`, `-listmedia`, `-listsoftware`, and `-romident` options can provide capability and identification inputs. `-listmedia` is driver-specific, and MAME uses configured ROM paths/system short names. Nested archives are not loadable as if their contents were top-level media. See the official [MAME command-line reference](https://docs.mamedev.org/commandline/commandline-all.html), [asset search rules](https://docs.mamedev.org/usingmame/assetsearch.html), and [software-list guidance](https://docs.mamedev.org/contributing/softlist.html).

### Privacy and distribution

- Do not commit, upload, attach to a PR, or include in build artifacts any ROM, BIOS, proprietary disk image, private catalog, or binary archive from the user's collection.
- Keep local catalogs out of version control by default and add ignore rules for generated catalogs if needed.
- Keep `verify_hash`, `verify_license`, read-only mounting, sandbox, and native-wrapper policies in force.
- Do not fetch ROMs or firmware automatically. A user-provided license declaration is metadata, not proof of legal rights.
- No binary found in the collection becomes trusted solely because it has a MAME-like filename.
- Do not publish the user's ROM folder or unverified emulator archives. Package only assets whose redistribution rights and binary provenance are verified per asset; prefer reproducible source builds and external release artifacts over adding large opaque binaries to Git history.

## Microkernel and Mobile Edition alignment

- Keep the media catalog and backend-capability schema portable so desktop and mobile Aurora views agree on system IDs, provenance state, and readiness states.
- Extend the existing `mobile/mobile-sync.json` shared-component contract and mobile validation workflow whenever a shared registry or launch-policy contract changes.
- On Mobile Edition, enumerate only emulators that are actually installed and allowed by that platform. Do not assume a desktop x86 MAME executable or its media support is present on Android, iOS, or a bare-metal mobile image. MAME-first applies only when the target build reports the selected system/media as supported; otherwise use a checked native fallback or report unsupported.
- Keep ROM/media access in an isolated user-space emulator service. The microkernel receives capability-scoped requests and must not scan ROM folders or handle media contents as part of startup.
- Mirror relevant registry, policy, UI, and tests into the existing Mobile Edition/Aurora Mobile surfaces in the same reviewed change set. Do not copy desktop-only binaries or the user's local catalog into `Mobile Microkernel` or mobile packages.

## ISO staging and optional redistributable media

The root `build-chimera-iso.sh` already has a `games` staging phase that copies the game registry and content under `ISO_DIR/games`. Extend that phase to stage the Aurora emulation registry, system/media metadata, and an empty `games/roms` directory so the generated image exposes the emulator section without requiring a library copy.

ROM payload inclusion is opt-in and allowlist-based. Accept a local `CHIMERA_ROM_ROOT` (including a Windows path translated for a WSL build) and a separately supplied redistribution manifest. Copy a file into `ISO_DIR/games/roms` only when the manifest identifies that exact relative path, SHA-256, license, and explicit redistribution permission; reject path traversal, symlink escapes, changed hashes, missing license data, and any unlisted file. The user's collection has not had per-file redistribution rights verified, so the default ISO build must not copy it. A local catalog is not an ISO distribution manifest.

Stage only the emulator binaries produced by the trusted source build/release flow and their license notices. Do not include the unverified emulator archive from the local collection. Track the allowlist/source fingerprint as part of the `games` stage resume state so changes cannot leave stale media in a resumed ISO. Report payload file count and bytes in the build report and account for them in the free-space estimate.

When an image contains approved media, expose its `games/roms` directory read-only to Aurora/MAME at runtime and keep installed user media separate. When the image contains no approved ROMs, the same emulator panel still opens against the user's configured local media root.

## Acceptance criteria

- Inventory is deterministic and reports partial/read errors without dropping prior catalog entries silently.
- Incremental refresh avoids hashing unchanged files when size and stable file identity permit it; a full verification mode recomputes hashes.
- Unit tests use synthetic media and a fake MAME executable/metadata fixture; they do not depend on or include user ROMs.
- Tests cover ambiguous extensions, per-driver MAME media support, missing/broken MAME, stale capability cache, checked fallback selection, malicious-looking paths/symlinks, unreadable files, and no launch for unverified executable archives.
- Aurora can browse the full registered system set and clearly distinguish MAME-ready, fallback-ready, unsupported, and policy-blocked items.
- Login/boot performs no recursive ROM scan or MAME-wide capability enumeration.
- A real MAME smoke check is reported separately from fake-MAME unit tests. Do not claim support for any local file unless the installed target MAME build confirms it.
- Mobile sync validation confirms the portable registry/policy is consistent with Mobile Edition; platform-specific backend availability remains capability-reported.
- Repository changes contain no local ROM/BIOS files or unverified emulator archives; any separately proposed redistributable asset has an explicit license/provenance record and repository-size review.
- Default ISO staging creates the emulator section but copies no ROM payload; an allowlisted test fixture is staged, while unlisted, modified, unlicensed, or path-escaping files are rejected.
- ISO build resume invalidates the games stage when its registry, allowlist, or payload fingerprint changes; the report records approved payload count/size.

## Out of scope

- Uploading or distributing local ROM/BIOS images, emulator archives, or the generated media index.
- Automatic downloading, archive extraction, firmware installation, or execution of unknown binaries.
- Replacing MAME or the existing checked emulator implementations.
- Adding ROM work to Koronos or the Aurora critical startup path.
- Porting every desktop emulator to mobile or promising mobile support for an unavailable backend.

