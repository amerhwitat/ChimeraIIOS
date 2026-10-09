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

## Acceptance gate status — 2026-10-09

- PDFreaderPY Java module: implementation and JUnit tests are committed; Java 17 Maven verification is **pending**, not yet marked passing.
- Acceptance-test PR: [PDFreaderPY #1](https://github.com/amerhwitat/PDFreaderPY/pull/1) adds coverage for quotes in evidence paths. Keep it open until a successful `Java PDF ingestion` workflow result is visible.
- Current execution limitation: the available execution environment has Java 21 but no Maven executable, and the project checkout/dependency cache is not mounted here. A real PDFBox 3.0.5 build cannot honestly be reported from this environment. The committed CI workflow is the required reproducible build gate; if it does not start automatically, run the workflow from GitHub Actions or push a follow-up commit to trigger it.
- Do not merge the acceptance PR or mark the Java module `build-passing` until `mvn --batch-mode --no-transfer-progress clean verify` succeeds. Fix compilation, dependency, fixture, or test failures before proceeding.
- Do not start broad new language ports until the first component passes this gate. Afterward, select one component with a stable API, add language-neutral fixtures, port it, and require build + parity tests before the next component.

### Latest CI evidence

- **Java PDF ingestion workflow:** run [37882326158](https://github.com/amerhwitat/PDFreaderPY/actions/runs/37882326158) completed successfully. Java 17 setup and `mvn --batch-mode --no-transfer-progress clean verify` both passed, including the original JUnit tests.
- **Python repository workflow:** run [37882326186](https://github.com/amerhwitat/PDFreaderPY/actions/runs/37882326186) failed because `tests/test_parallel_search.py` imported a missing root-level `performance` module (`ModuleNotFoundError: No module named 'performance'`). Added `performance.py` with deterministic, case-insensitive parallel page search and source-order results in commit `a50408f9598d5901928e73a0a38c369ce295ccb6`.
- **Final combined acceptance PR:** [PDFreaderPY #2](https://github.com/amerhwitat/PDFreaderPY/pull/2) is open to rerun Java and Python CI together against the fixed main branch. Do not merge until both checks have fresh successful results. Latest workflow lookup has not yet returned runs for this new PR, so the combined gate is still pending.

### Acceptance gate completed — PDFreaderPY

- Python repository workflow [run 85](https://github.com/amerhwitat/PDFreaderPY/actions/runs/37882418056) passed after restoring `performance.py` and deterministic parallel search behavior.
- Java PDF ingestion workflow [run 7](https://github.com/amerhwitat/PDFreaderPY/actions/runs/37882418098) passed: Java 17 setup and Maven `clean verify`, including PDFBox rendering, provenance, invalid-page/input handling, and quoted-path JSON escaping.
- Acceptance PR [#2](https://github.com/amerhwitat/PDFreaderPY/pull/2) was merged successfully as commit [`f17f33f`](https://github.com/amerhwitat/PDFreaderPY/commit/f17f33fe169a1154f32a4615ca5878327e0ceac3).
- Status: PDFreaderPY Java ingestion is **build-passing and regression-tested for the current scope**. This does not claim OCR parity; scanner integration remains explicitly `not-run` until a scanner adapter is implemented.

### Next dependency-consistent component

Proceed to the existing ChimeraIIOS Java driver-acquisition layer next. Confirm its actual tracked source paths, run the documented `javac`/test command in CI, and add contract tests for allowlisting, redirect refusal, download-size limits, SHA-256 verification, and atomic staging. Do not mark the driver layer passing until that job succeeds. Afterward, audit the next repository independently rather than converting unrelated applications into a single Java program.

### ChimeraIIOS driver-acquisition gate result

- Dedicated Java workflow [run 2](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/37882484035) passed on Java 21: all tracked `java/chimera/**/*.java` sources compiled with `javac -Xlint:all -Werror`, and `chimera.drivers.acquisition.DriverAcquisitionManagerTest` completed successfully.
- CI gate PR [#56](https://github.com/amerhwitat/ChimeraIIOS/pull/56) was merged as [`f285d76`](https://github.com/amerhwitat/ChimeraIIOS/commit/f285d76d75c4902cc6f241374a707b2dc663fa74).
- The broader Chimera II CI/CD run [3940](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/37882484039) was still running at the time of this update; its native build/test jobs are tracked separately from the dedicated Java gate and should be checked before claiming the entire OS pipeline is green.


### BizX Java runtime contract gate — merged

- Audited `java/src/main/java/io/amerhwitat/bizx/UnifiedBizXRuntime.java`, `GameLauncher.java`, the Maven build, and the existing chess/strategy, crypto-wallet, and AAA system contracts. The audited Java facade's current public surface includes an ordered feature list, UTF-8 SHA-256, and game-mode normalization; this is not evidence of complete Java parity for all BizX subsystems.
- Added shared language-neutral vectors at `amerhwitat/BizX/contracts/fixtures/bizx-runtime-v1.tsv`, consumed by a JUnit test. Added Java 17 Maven CI in `amerhwitat/BizX/.github/workflows/java-runtime-contracts.yml`.
- Fixed an existing Java test compile failure by using `PlayerResources.Checkpoint`, and corrected the test flow to reflect health-prompt priority and the magazine/reserve-ammo state machine.
- Repository validation exposed missing Python compatibility imports. Restored `python/bizx/modules/crypto.py` and `network.py`; crypto intents are unsigned and provider-bound, and loopback classification is covered by the existing Python tests.
- Fixed root `build.sh` to invoke `scripts/build.sh` through Bash instead of depending on its executable bit.
- [BizX PR #4](https://github.com/amerhwitat/BizX/pull/4) merged as [`d90e16d`](https://github.com/amerhwitat/BizX/commit/d90e16dd81731c1e779ae1b35d53acd81c37b98a).
- Dedicated Java 17 Maven `clean verify` passed in [workflow run 13](https://github.com/amerhwitat/BizX/actions/runs/37883057958). Python repository validation passed in [run 492](https://github.com/amerhwitat/BizX/actions/runs/37883057918). The gameplay resource checks also passed in [run 421](https://github.com/amerhwitat/BizX/actions/runs/37883054076).
- **Cross-platform aggregate build remains pending**: [Build all applications run 322](https://github.com/amerhwitat/BizX/actions/runs/37883057891) was still running on Windows/Linux/macOS when this update was written. The prior matrix exposed a non-executable `scripts/build.sh`; the wrapper was fixed in the merged change, but the full matrix must finish before its status can be called green.

### Next Java portfolio gates

1. **BizXtreme:** inspect its actual Java source tree, public contracts, JDK baseline, and current tests; add shared deterministic fixtures before expanding behavior.
2. **CPU4096:** compare Java arithmetic/register model and benchmark behavior against shared vectors and existing non-Java implementations.
3. **CPU4096Simulator:** validate simulator trace/register-state parity and its JavaFX runtime separately from the CPU core.
4. Merge each stage only when its dedicated build and parity tests pass. Keep the original implementations and mark only the verified scope as complete.


### Follow-up cross-platform validation findings — BizX

- The Java acceptance gate remains green at [BizX Java workflow run 13](https://github.com/amerhwitat/BizX/actions/runs/37883057958); Python repository validation and gameplay resource checks passed on the corresponding acceptance commits.
- The aggregate build exposed two pre-existing non-Java test/contract issues. [BizX PR #5](https://github.com/amerhwitat/BizX/pull/5) corrected an email-extraction assertion that incorrectly dropped a distinct address at the same domain; it merged as [`ae0d2ea`](https://github.com/amerhwitat/BizX/commit/ae0d2eac1b70d09c4684ed0ef136b36c3c2c5f1b).
- The next aggregate run exposed InternetScanner test issues: a local TCP fixture's expected teardown reset was unhandled, and one test imported obsolete export names (`classify`/`authorized`) instead of the current public names (`classifyIp`/`authorizedTarget`). [BizX PR #6](https://github.com/amerhwitat/BizX/pull/6) addresses both test-contract problems; its CI is pending at the time of this update. Do not mark the BizX aggregate cross-platform build green until its latest matrix finishes successfully.

### BizXtreme Java acceptance gate — merged

- Audited the Java launcher, `BizXtremeApi`, and `BizXtremeCore`. The documented launcher instantiated `new BizXtremeApi()`, but the class only exposed a constructor requiring a core. Added a safe default constructor using the default `BizXtremeCore`, with null-core rejection.
- Added shared health-contract vectors at `amerhwitat/BizXtreme/contracts/fixtures/bizxtreme-runtime-v1.tsv`, a JUnit fixture-driven test, and a Java 17 Maven workflow.
- Fixed the pre-existing Java resource test to use `PlayerResources.Checkpoint` and to exhaust reserve ammo according to actual reload semantics. Fixed the Node.js survival-resource test's incorrect expectations for ammo return values and health-prompt priority.
- [BizXtreme PR #3](https://github.com/amerhwitat/BizXtreme/pull/3) merged as [`fe1a9bd`](https://github.com/amerhwitat/BizXtreme/commit/fe1a9bde75561b837d80d88f249400dda36c57f4).
- Java 17 Maven verification passed in [BizXtreme Java workflow run 5](https://github.com/amerhwitat/BizXtreme/actions/runs/37883415454). Cross-language gameplay resource checks passed in [run 184](https://github.com/amerhwitat/BizXtreme/actions/runs/37883415451). This verifies the API/core health contract and resource state machine only, not complete wallet/WebGL/Three.js parity.

### CPU simulator repositories — next audit

- `amerhwitat/CPU4096` documents a Java 21 register-model visualization/benchmark layer; no `java/pom.xml` was found at the documented root path during this pass.
- `amerhwitat/CPU4096Simulator` documents a JavaFX trace/dashboard layer and shared deterministic JSON/JSONL vectors; no `java/pom.xml` was found at the documented root path during this pass.
- Next, inventory the actual tracked Java source/build layout before creating fixtures. Define vectors for fixed-width wraparound, shifts, register snapshots, deterministic trace ordering, and metadata reproducibility only after confirming the implementations' actual public APIs. Do not claim ISA conformance from an opcode catalog alone.


### BizX follow-up gate update

- [BizX PR #6](https://github.com/amerhwitat/BizX/pull/6) is now merged as [`80564f3`](https://github.com/amerhwitat/BizX/commit/80564f3e86e5df0edb822fd626d93912fd15b8b8). Its dedicated InternetScanner Node validation [run 19](https://github.com/amerhwitat/BizX/actions/runs/37883577441) passed after aligning test imports with the actual exports and handling expected TCP fixture teardown errors.
- The aggregate cross-platform matrix [run 327](https://github.com/amerhwitat/BizX/actions/runs/37883577410) was still running on Linux, Windows, and macOS at this check. The Java gate, Python repository validation, gameplay resource checks, email sender validation, and InternetScanner Node contract checks have passed in their dedicated runs, but the aggregate matrix remains **unverified** until run 327 completes.


### CPU4096 source audit and Java register acceptance gate

- Used the recursive Git tree, not guessed paths. `CPU4096/java/` contained only `README.md`; the real native register contract is `RegisterN<Bits>` in `RegisterN.hpp`, and the Node snapshot contract is `registerSnapshot()` in `node/src/index.js`.
- [CPU4096 PR #2](https://github.com/amerhwitat/CPU4096/pull/2) adds a Java 21 `RegisterN` model, Maven/JUnit acceptance gate, and shared vectors for addition, modulo wraparound, subtraction wraparound, shifts, and least-significant-word-first snapshots. The Node test also consumes the snapshot vector.
- This implements a tested register semantic subset; it does not mean the documented Java GUI/benchmark layer already existed or is now implemented. PR CI is pending at this tracker update.

### CPU4096Simulator source audit and Java core acceptance gate

- The recursive Git tree showed `CPU4096Simulator/java/` contained only `README.md`. The real simulator API is `WideWord`/`CpuCore` in `src/chimera.js`; the existing public tests are in `test/core.test.mjs`. There was no JavaFX source or Java build file to test.
- [CPU4096Simulator PR #2](https://github.com/amerhwitat/CPU4096Simulator/pull/2) adds a Java 21 headless `WideWord` and `CpuCore`, Maven/JUnit CI, and shared vectors for modular arithmetic, shifts, snapshots, instruction trace order/PC advancement, and stable workload-envelope metadata. Java and Node tests consume the same TSV fixtures.
- This verifies only the explicitly implemented opcode subset (ADD, SUB, MOV, SHL, SHR) and 16-byte little-endian encoding. It does not claim a JavaFX dashboard, full opcode parity, or ISA conformance. PR CI is pending at this tracker update.

### BizX aggregate matrix follow-up

- The previous aggregate run [331](https://github.com/amerhwitat/BizX/actions/runs/37892479111) is executing after [PR #8](https://github.com/amerhwitat/BizX/pull/8) addressed the observed Linux script permission failure, Jest-vs-Node test runner mismatch, and AGP 9.4 redundant Kotlin plugin error. Repository validation [run 501](https://github.com/amerhwitat/BizX/actions/runs/37892479099) and gameplay resource checks [run 431](https://github.com/amerhwitat/BizX/actions/runs/37892479187) passed. Do not merge PR #8 or mark the cross-platform aggregate green until run 331 completes successfully.


### CPU acceptance gates — merged and green

- **CPU4096:** [PR #2](https://github.com/amerhwitat/CPU4096/pull/2) merged as [`3607a94`](https://github.com/amerhwitat/CPU4096/commit/3607a945630fa222c6822cae4301699db7964d47). Java 21 Maven/JUnit register vectors passed in [run 1](https://github.com/amerhwitat/CPU4096/actions/runs/37892784901), including the Node snapshot-fixture parity job. The gate covers modulo arithmetic, shifts, and little-endian word snapshots.
- **CPU4096Simulator:** [PR #2](https://github.com/amerhwitat/CPU4096Simulator/pull/2) merged as [`7c4863d`](https://github.com/amerhwitat/CPU4096Simulator/commit/7c4863d2f9eebdf2971c26c6018829033f3880a7). Java 21 Maven/JUnit vectors passed in [run 1](https://github.com/amerhwitat/CPU4096Simulator/actions/runs/37892736926), and the existing Node web CI passed on the same PR head in [run 335](https://github.com/amerhwitat/CPU4096Simulator/actions/runs/37892736795). Shared fixtures cover arithmetic wraparound, shifts, snapshot formatting, trace order/PC advancement, and stable workload metadata.
- Both audits confirmed that the original `java/` directories contained only README files; the new headless Java register/core implementations are real new implementations, not a conversion of previously existing JavaFX code. Full JavaFX visualization, the complete opcode set, and architectural/ISA conformance remain separate work.

### BizX aggregate build — latest retry pending

- [PR #8](https://github.com/amerhwitat/BizX/pull/8) now also fixes the web test import path, adds an explicit microphone-permission guard, and makes the aggregate runner report unsupported SDK/platform work as skipped instead of failing on Linux/macOS for Windows-only WPF/.NET Framework/Visual C++ targets or an absent Dart SDK.
- The latest aggregate run is [run 335](https://github.com/amerhwitat/BizX/actions/runs/37892956578); it was queued when checked. The repository validation [run 505](https://github.com/amerhwitat/BizX/actions/runs/37892956532) passed. Do not merge PR #8 until the latest aggregate Linux/Windows/macOS matrix passes. Skipped platform-specific work remains unverified rather than being reported as tested.
