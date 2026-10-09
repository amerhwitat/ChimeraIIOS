# Java Portfolio Migration — Initial Audit and Execution Plan

Date: 2026-10-09

## Objective

Provide a maintained Java implementation for each applicable project while preserving behavioral parity, tests, licenses, and platform boundaries. This is an incremental porting program, not a blind extension-renaming pass. A repository is not considered Java-complete until its Java sources build and its shared conformance tests pass.

## Initial repository survey

This first survey inspected repository metadata, root README files, Java README files where present, and targeted GitHub code-search results. Search indexing returned no Java matches for several repositories, so absence of a search result is **not** proof that a repository contains no Java source.

| Repository | Initial Java evidence | Next engineering step |
|---|---|---|
| `amerhwitat/ChimeraIIOS` | Existing `java/chimera/drivers/` layer mirrors a Python driver-acquisition contract | Continue Python/Java parity; add bounded downloads, redirect protection, and policy regression tests |
| `amerhwitat/BizX` | `java/` unified runtime documented; Maven build documented | Inventory modules and test API parity against shared contracts |
| `amerhwitat/BizXtreme` | Java launcher, API, game, wallet, crypto, WebGL and Three.js boundaries documented | Run Maven tests and expand shared deterministic contract tests |
| `amerhwitat/CPU4096` | Java GUI/benchmark layer documented alongside C++, Node.js and Python | Verify arithmetic/register-model parity and shared vectors |
| `amerhwitat/CPU4096Simulator` | JavaFX visualization layer documented alongside JS/Node/C++ | Verify simulator trace and register-state parity |
| `amerhwitat/keygen` | Repository README identifies a Java 25/Koronos implementation track | Audit JVM runtime semantics and tests; retain native boot boundaries |
| `amerhwitat/bruteforce` | Java 21 research/GUI layer documented | Preserve safe crypto research boundary; only public/synthetic vectors and restore-and-verify workflows |
| `amerhwitat/eth-key-check` | README identifies a Java implementation directory | Audit cross-language validation and public-address verification parity |
| `amerhwitat/nlp` | Python, C++, .NET, desktop and web implementations documented; no `java/README.md` found in this pass | Add a Java text-processing API against shared, licensed test fixtures and Unicode normalization contracts |
| `amerhwitat/PDFreaderPY` | Python/PyMuPDF reference; a new Java 17+/PDFBox page-rendering and evidence-provenance module now exists in `java/` | Build it and add PDF fixture parity tests; OCR remains an explicit separate adapter |
| `amerhwitat/amerhwitat.github.io` | Public browser/web surface; no `java/README.md` found in this pass | Keep browser UI in web-native code; add Java only for server-side services where needed |
| `amerhwitat/general` | Integration workspace with multiple projects; no root `java/README.md` found in this pass | Inventory each subproject independently rather than flattening unrelated applications into one Java program |
| `amerhwitat/test` | Python research/integration and conformance target; no `java/README.md` found in this pass | Port stable host-side contracts first and reuse shared fixtures |
| `amerhwitat/VanG` | Private repository; no root `java/README.md` found in this pass | Audit only through authorized repository access and preserve its private-source boundary |

## Porting rules

1. **Inventory before conversion.** Record language, entry point, external dependencies, public API, license, tests, generated/vendor code, and target platforms before porting a component.
2. **Use parity implementations, not file renames.** Each Java port must preserve documented inputs, outputs, errors, encoding, persistence format, and security checks.
3. **Share conformance fixtures.** Prefer language-neutral JSON/JSONL vectors and deterministic tests over duplicated undocumented behavior.
4. **Preserve native boot/runtime boundaries.** Bare-metal firmware, GRUB/Jasper/Spit Fire loaders, interrupt entry, hardware drivers and the freestanding Koronos kernel cannot be replaced by ordinary JVM code before a JVM exists. Java implementations should provide host-side models, tools, services, and post-boot runtime layers.
5. **Respect platform-specific code.** Browser JavaScript, SwiftUI, C/C++ ABI bindings, and device APIs should be replaced only where an equivalent Java target exists; otherwise provide explicit adapters and keep the source of record.
6. **Do not copy third-party code without license/provenance checks.** Reuse existing open-source Java implementations only when their license is compatible and attribution is retained.
7. **No false completion claims.** Track each component as `inventoried`, `ported`, `build-passing`, `parity-tested`, or `platform-verified`.

## Current implementation update

The existing Chimera II Java driver acquisition layer was brought closer to its Python contract:

- Host allowlist is normalized case-insensitively and an empty allowlist is rejected.
- A configurable maximum download size is enforced while streaming to a temporary file.
- HTTP redirects are disabled to prevent an allowlisted URL from redirecting the download to an untrusted host.
- The downloaded file is SHA-256 checked before atomic staging into its destination.
- Regression checks cover the configured size limit, host allowlisting, empty policy and digest mismatch.

Build/test command documented by the existing Java layer:

```sh
javac -d build $(find java/chimera -name '*.java')
java -cp build chimera.drivers.acquisition.DriverAcquisitionManagerTest
```

This command must be run in a JDK-equipped environment before this Java change is marked build-passing. The PDFreaderPY Java page-ingestion port is also committed in `amerhwitat/PDFreaderPY/java/`; it deliberately marks scanner execution as `not-run` until a Java scanner adapter is configured. The broader portfolio conversion remains in progress.

### PDFreaderPY Java verification gate

The Java page-ingestion module now includes JUnit tests for a generated two-page PDF, selected-page rendering, evidence provenance, out-of-range page rejection, and missing input rejection. A repository-local GitHub Actions workflow runs `mvn --batch-mode --no-transfer-progress clean verify` on Java changes and pull requests. The workflow has been committed but its first run must finish successfully before this module is marked `build-passing`; this document does not claim that tests have already passed.

### Portfolio-wide next gates

- [ ] Discover exact source trees and build entry points for every repository (GitHub code search may omit unindexed files).
- [ ] Run each existing Java build and record JDK/toolchain requirements.
- [ ] Add language-neutral fixtures for each stable public contract before porting behavior.
- [ ] Port one dependency-consistent component at a time; keep the original implementation until parity tests pass.
- [ ] Add repository-local CI gates and record commit SHA + test result for each completed component.
- [ ] Audit Java dependency licenses, supply-chain posture, and supported JDK versions.
- [ ] Keep bare-metal boot and kernel paths native until a JVM runtime can actually be launched.
