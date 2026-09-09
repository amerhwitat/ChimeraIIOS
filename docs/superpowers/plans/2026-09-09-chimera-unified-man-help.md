# Chimera II Unified Linux + Microsoft Help System

**Date:** 2026-09-09  
**Execution mode:** Subagent-Driven Development (SDD)  
**Repository:** `amerhwitat/ChimeraIIOS`  
**Base:** `main`

## Goal

Extend the existing Chimera II manual/help subsystem so `man`, `apropos`, `whatis`, `info`, shell `help`, and command `--help` can resolve a unified documentation namespace from Linux/POSIX/BSD/System V/Bash/Zsh material, Microsoft/Windows/CMD/PowerShell material, compiler/toolchain documentation, and Chimera II documentation. The same backend must serve native terminals, Web Terminal, and the Aurora Wayland/Web desktop.

The implementation must scale to complete documentation sets supplied by supported Linux distributions and must not pretend that every distribution's manuals are identical or that all Microsoft documentation is freely redistributable. Microsoft material is represented through licensed local help where permitted and official documentation references/cache entries otherwise.

## Architecture

```text
                         Chimera Help API
                               |
                    +----------+----------+
                    |                     |
              Help Resolver          Help Search
                    |                     |
              SQLite + FTS5       provenance/index
                    |
        +-----------+------------+----------------+
        |           |            |                |
     Linux Man   Microsoft    Toolchain       Chimera II
     adapters    adapters      adapters         docs
        |           |            |                |
 /usr/share/man  Win/PS help  GCC/Clang/etc.  docs/web catalogs
 package sets    official URLs  local manuals   ISA/OS docs
        +-----------+------------+----------------+
                    |
          Native CLI / Web API / Aurora UI
```

### Canonical document model

Every indexed document has a stable identifier and metadata:

- `id`
- `namespace` (`linux`, `posix`, `bsd`, `sysv`, `bash`, `zsh`, `microsoft`, `windows`, `powershell`, `toolchain`, `chimera`)
- `name`
- `section`
- `title`
- `synopsis`
- `summary`
- `content_uri` or local path
- `source_uri`
- `source_version`
- `platform`
- `locale`
- `license`
- `checksum`
- `last_updated`
- `availability` (`local`, `remote`, `hybrid`)

### Resolution rules

1. Preserve standard `man PAGE`, `man SECTION PAGE`, `apropos`, and `whatis` behavior.
2. Add explicit namespaces: `man linux:ls`, `man microsoft:cmd`, `man powershell:Get-Process`, `man chimera:chimera-isa`.
3. Resolve aliases and section-qualified names deterministically.
4. Prefer local licensed content; otherwise expose official-source metadata/link without copying restricted text.
5. Keep the current `web/man_pages.json` catalog as a compatibility seed, not as the complete documentation database.
6. `help` and `--help` integration must use the same resolver and must never execute arbitrary commands merely to obtain documentation.

## Tech Stack

- C++17+ core library for the native Chimera runtime/tooling.
- SQLite with FTS5 for the portable local documentation index.
- JSON manifests for source configuration, compatibility catalogs, and provenance.
- Existing Web UI JavaScript/HTML/CSS contracts under `web/`.
- POSIX/Linux compressed-man parsing (`.gz`, `.xz`, `.zst`) through isolated adapters.
- Windows path/process abstraction without requiring a Linux host at runtime.
- CMake/CTest for native builds/tests.
- Python helper tools only where they simplify ingestion/index generation; no runtime dependency on Python for the core CLI.

## Spec

### Existing repository contracts to preserve

- `web/man_pages.json` currently uses schema `chimera-man-db/v1` and already covers POSIX/Linux/BSD/System V/Bash/Zsh/PowerShell/Windows CMD/Chimera II command metadata.
- `web/command_catalog.json` and `web/aurora_terminal_profile.json` remain compatible.
- Aurora is one desktop surface shared by native Wayland and Web UI.
- The terminal remains virtualized/sandboxed: no arbitrary host shell, network, or destructive execution from Web/Aurora documentation features.
- Existing Chimera CISC/RISC compiler and ISA tooling names remain resolvable.

### Required command surface

```text
man [SECTION] PAGE
man NAMESPACE:PAGE
man --source SOURCE PAGE
man --all PAGE
apropos KEYWORD...
whatis COMMAND...
info [MENU-ITEM...]
help [COMMAND]
COMMAND --help
chimera-help <subcommand>
```

`chimera-help` must provide at least `search`, `show`, `sources`, `update`, `verify`, and `doctor` subcommands.

### Linux coverage

Support ingestion of complete installed man-page sets from standard filesystem locations and package-produced sets, including common section families `1` through `9`, local extension sections, aliases, compressed pages, and locale directories. Provide source manifests for major Linux packaging families without bundling every distro's manuals into the Git repository.

The indexer must be incremental, checksum-aware, and safe for very large documentation sets.

### Microsoft coverage

Support:

- Windows CMD command help.
- PowerShell command/help metadata and local help when available.
- Win32/.NET/Windows developer documentation references.
- Official Microsoft documentation links for material that cannot be redistributed.
- Provenance and licensing metadata for every imported Microsoft entry.

Do not wholesale copy Microsoft copyrighted manuals into the GPL repository unless the specific material is verified as redistributable under compatible terms.

### Terminal integration

The native Chimera shell, Bash/Zsh compatibility layer, Web Terminal, and Aurora Terminal must invoke the same logical help resolver. Web/Aurora requests are read-only and sandboxed. Native privileged adapters are separate from the documentation service.

### Web integration

Expose a small read-only API contract:

- `GET /api/help/search?q=...&namespace=...&section=...`
- `GET /api/help/page/{id}`
- `GET /api/help/sources`
- `GET /api/help/status`

The browser UI must show title, synopsis, source, version, license/provenance, section, content, and official external-source links where applicable.

### Aurora integration

Add a Help/Man application to the Aurora application registry and expose it through the existing glass desktop surface. It must support keyboard navigation, search, section filtering, namespace filtering, copy-safe code blocks, and external official documentation links.

## Global Constraints

1. Preserve existing ABI and command-catalog compatibility.
2. Do not replace the current compact `web/man_pages.json`; extend it through versioned compatibility/migration logic.
3. No arbitrary host command execution from Web/Aurora help features.
4. No privileged filesystem mutation from documentation search/view operations.
5. Do not claim to ship every Linux distribution manual; provide scalable ingestion and manifests for supported sources.
6. Do not redistribute restricted Microsoft documentation text without a verified license; use official links/metadata when necessary.
7. Maintain deterministic tests and offline operation for already-indexed local content.
8. Keep C++ production baseline compatible with the repository's existing CMake configuration.
9. Preserve existing security/audit command restrictions.
10. Maintain UTF-8 and RTL-safe rendering in Web/Aurora interfaces.

## Task 1 — Core help data model and resolver

**Files:**
- `include/chimera/help_database.hpp` (new)
- `include/chimera/help_resolver.hpp` (new)
- `src/help/help_database.cpp` (new)
- `src/help/help_resolver.cpp` (new)
- `tests/help/test_help_resolver.cpp` (new)

**Implementation:**
- Define the canonical document/source structures.
- Implement SQLite/FTS5 schema creation and migration from `chimera-man-db/v1` JSON.
- Implement deterministic namespace/section/alias resolution.
- Implement `search`, `show`, `sources`, and `status` library interfaces.
- Add exact tests for section precedence, aliases, namespaces, duplicate names, missing pages, and migration.

**Verification:**
```bash
cmake -S . -B build -DCHIMERA_ENABLE_EXPERIMENTAL=ON
cmake --build build --parallel
ctest --test-dir build -R help_resolver --output-on-failure
```

## Task 2 — Linux man-page ingestion

**Files:**
- `tools/help/linux_man_indexer.py` (new)
- `tools/help/linux_sources.json` (new)
- `tests/help/test_linux_man_indexer.py` (new)
- `docs/help/LINUX_MAN_DATABASE.md` (new)

**Implementation:**
- Walk configurable man roots and locale trees.
- Parse normal and compressed pages without requiring `man` itself.
- Extract section/name/title/synopsis where safely detectable and retain raw local path for full-page display.
- Support incremental checksum indexing.
- Define distro/package-family source manifests for Debian/Ubuntu, Fedora/RHEL-compatible, Arch, Alpine, openSUSE, Gentoo, and generic `/usr/share/man` layouts.
- Never assume one distro's manual set represents another distro.

**Verification:**
- Build a temporary fixture containing sections 1, 5, and 8 plus `.gz`, `.xz`, and `.zst` fixtures where available.
- Assert stable IDs, section parsing, duplicate handling, checksum skip behavior, and locale selection.

## Task 3 — Microsoft/Windows/PowerShell adapter

**Files:**
- `include/chimera/help_microsoft.hpp` (new)
- `src/help/help_microsoft.cpp` (new)
- `tools/help/microsoft_sources.json` (new)
- `tests/help/test_microsoft_help.cpp` (new)
- `docs/help/MICROSOFT_WINDOWS_HELP.md` (new)

**Implementation:**
- Define local-help discovery for Windows/CMD/PowerShell where permitted.
- Define official Microsoft URL records for Windows/Win32/.NET/PowerShell documentation.
- Record license/provenance and distinguish `local`, `remote`, and `hybrid` entries.
- Prevent the ingestion layer from silently copying restricted remote content.

**Verification:**
- Offline tests use fixtures only.
- Verify every source record has provenance and redistribution status.
- Verify remote-only records resolve to official links without pretending local content exists.

## Task 4 — Unified CLI and shell integration

**Files:**
- `src/userspace/chimera_help.cpp` (new or existing help command integration point)
- `userspace/shell/chimera_shell.cpp` (update if present)
- `tools/help/chimera-help` (new executable/script wrapper as appropriate)
- `tests/help/test_help_cli.py` (new)
- `docs/help/CLI_HELP.md` (new)

**Implementation:**
- Implement `man`, `apropos`, `whatis`, `info`, `help`, and `chimera-help` over the shared resolver.
- Preserve native shell behavior when a real host `man` is available, while providing Chimera namespace resolution.
- Add safe `COMMAND --help` catalog lookup that does not execute untrusted binaries.
- Add pager abstraction with plain-terminal fallback.

**Verification:**
```bash
python3 tests/help/test_help_cli.py
```

Test all required command forms, namespaces, sections, aliases, unknown commands, and offline mode.

## Task 5 — Web Terminal API and UI

**Files:**
- `web/help/help_api.js` (new)
- `web/help/help_viewer.js` (new)
- `web/help/help.css` (new)
- `web/help/help_manifest.json` (new)
- `web/cli_terminal.js` (update)
- `web/command_catalog.json` (update only where necessary)
- `tests/help/test_web_help_contract.py` (new)

**Implementation:**
- Reuse the same logical resolver contract rather than maintaining a second database in JavaScript.
- Add search/show/source/status endpoints or a browser adapter for the configured backend.
- Add namespace/section filters, provenance badges, official-source links, and keyboard navigation.
- Keep all documentation actions read-only and sandboxed.

**Verification:**
- JSON contract tests validate stable response shapes.
- Verify no Web Terminal help action invokes arbitrary host shell/network APIs.

## Task 6 — Aurora Desktop Help application

**Files:**
- `web/aurora_apps.json` (update)
- `web/aurora_desktop_surface.js` (update)
- `desktop/aurora/aurora-help.desktop` (new)
- `desktop/aurora/aurora-help.sh` (new)
- `docs/help/AURORA_HELP.md` (new)
- `tests/help/test_aurora_help_contract.py` (new)

**Implementation:**
- Register Help/Man as a first-class Aurora app.
- Reuse the Web Help Viewer contract and preserve the glass desktop/window model.
- Add deep-link support from terminal results into the Help application.
- Provide a native Wayland launcher while retaining Web UI compatibility.

**Verification:**
- Validate app registration, launcher metadata, deep links, and no unrestricted execution path.

## Task 7 — Update, provenance, packaging, and documentation

**Files:**
- `tools/help/chimera_help_update.py` (new)
- `tools/help/help_sources.lock.json` (new)
- `tests/help/test_help_update.py` (new)
- `docs/help/README.md` (new)
- `docs/help/SECURITY_AND_LICENSE.md` (new)
- `README.md` (update)
- `CMakeLists.txt` (update only where required)

**Implementation:**
- Add `chimera-help update` with dry-run mode, checksum verification, atomic index replacement, and source manifests.
- Keep remote Microsoft documentation as links/metadata unless redistribution is explicitly allowed.
- Add reproducible index metadata and health diagnostics.
- Document how to install complete Linux manual sets using the host distribution's package manager and then index them.
- Document Windows installation behavior and offline/online modes.

**Verification:**
```bash
python3 tests/help/test_help_update.py
ctest --test-dir build --output-on-failure
```

## Task 8 — Full integration and regression review

**Files:**
- `tests/help/test_help_integration.py` (new)
- `docs/help/INTEGRATION_MATRIX.md` (new)
- `.github/workflows/` existing CI workflow updated only if needed

**Implementation:**
- Test native CLI, Web Terminal, Aurora, Linux sources, Microsoft sources, toolchain entries, and Chimera entries against one canonical namespace contract.
- Verify migration from existing `web/man_pages.json`.
- Verify empty/offline/corrupt-source behavior.
- Verify security boundaries and provenance.

**Verification:**
```bash
cmake -S . -B build -DCHIMERA_ENABLE_EXPERIMENTAL=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
python3 tests/help/test_help_integration.py
python3 tests/installer/test_installer_plan.py
python3 tests/cognition/test_chimera_rnn.py
```

## Task Dependency / Shared-Interface Scan

| Task | Produces | Consumes | Conflict check | Ruling |
|---|---|---|---|---|
| 1 | canonical DB/resolver API | existing v1 JSON contract | Base interface for all later tasks | Resolver is authoritative; existing JSON is migration input only. |
| 2 | Linux source/index records | Task 1 source/document model | Shared DB schema | Linux adapter owns ingestion; resolver owns lookup. |
| 3 | Microsoft source/index records | Task 1 source/document model | Licensing differs from Linux | Remote-only Microsoft records are metadata/link objects, never fake local pages. |
| 4 | CLI command surface | Task 1 resolver | `man` already exists in catalog | Preserve current command names and extend resolution. |
| 5 | Web help API/view | Task 1 resolver + Task 4 command semantics | Browser must not become a second resolver | Web consumes canonical API; no duplicated search logic. |
| 6 | Aurora app | Task 5 Web viewer + existing Aurora contracts | Aurora and Web are one surface | Aurora embeds/reuses the same viewer contract. |
| 7 | update/provenance | Tasks 1–3 | Updates could invalidate index | Atomic index replacement and checksum validation prevent partial state. |
| 8 | integration tests | Tasks 1–7 | CI could expose cross-layer mismatch | Canonical command/source contract is tested end-to-end. |

### Per-task self-consistency scan

| Task | Files vs tests | Interface consistency | Ruling |
|---|---|---|---|
| 1 | Tests target resolver/DB interfaces created by the task | Consistent | Proceed. |
| 2 | Python indexer tests target the same parser/index manifest | Consistent | Proceed. |
| 3 | C++ adapter and fixture tests target local/remote distinction | Consistent | Proceed. |
| 4 | CLI tests target all specified commands | Consistent | Proceed. |
| 5 | Web contract tests target the declared API/view | Consistent | Proceed. |
| 6 | Aurora contract tests target registered app/deep links | Consistent | Proceed. |
| 7 | Update tests target manifests/checksums/atomic behavior | Consistent | Proceed. |
| 8 | Integration tests consume all prior contracts | Consistent | Proceed. |

## Security and licensing decisions

- Documentation search is data access, not command execution.
- Web/Aurora documentation operations are read-only.
- Remote Microsoft sources are represented by official links and metadata unless explicit redistribution rights are established.
- Linux manual ingestion is performed from user-installed/package-provided local data rather than assuming the repository can legally redistribute every distribution's manuals.
- Source checksums and provenance are first-class fields so stale or altered documentation can be diagnosed.

## Acceptance criteria

The work is accepted only when:

1. `man`, `apropos`, `whatis`, `info`, `help`, and `chimera-help` share one resolver model.
2. Existing `web/man_pages.json` entries remain resolvable.
3. Complete installed Linux man-page sets can be indexed incrementally from supported filesystem/package layouts.
4. Microsoft/CMD/PowerShell help can resolve local permitted content and official documentation references without unauthorized wholesale redistribution.
5. Native terminal, Web Terminal, and Aurora Help use the same namespace and provenance semantics.
6. Web/Aurora documentation features cannot invoke arbitrary host commands.
7. CMake/CTest and all new Python integration tests pass.
8. Documentation explains installation, update, offline operation, licensing, provenance, and security boundaries.
9. No existing ABI is intentionally changed.
10. The repository status remains explicitly a research/engineering prototype and does not claim undocumented host or hardware capabilities.
