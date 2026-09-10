# BizX Java and Python Implementations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add first-class Java and Python implementations to BizX and BizXtreme and synchronize language-specific documentation and Chimera II OS integration documentation.

**Architecture:** Java and Python are isolated by top-level language directories. Each implementation exposes a small native core, wallet/provider boundary, subsystem modules, tests, and build metadata without mixing source languages. Existing Node.js, browser JavaScript, TypeScript, Unity/C#, and packaged artifacts remain intact.

**Tech Stack:** Java 17+, Maven; Python 3.10+, standard library; Node.js remains Node 20+; Markdown/JSON documentation.

**Spec:** Approved chat design for language-separated BizX/BizXtreme implementations.

## Global Constraints

- Java source lives only under `java/` in BizX/BizXtreme.
- Python source lives only under `python/` in BizX/BizXtreme.
- Java uses Maven and Java 17+.
- Python uses Python 3.10+ and a dependency-light package layout.
- Existing packaged APK/WebGL artifacts are preserved.
- Root and language-specific README files must document the implementation matrix.
- Chimera II OS consumes BizX/BizXtreme through user-space integration boundaries.

---

### Task 1: BizX Java implementation

**Files:** `BizX/java/pom.xml`, `BizX/java/README.md`, `BizX/java/src/main/java/...`, `BizX/java/src/test/java/...`

- [ ] Add Maven metadata and Java-native core/wallet/catalog/payments/api/cli modules.
- [ ] Add unit tests for core health and wallet JSON-RPC forwarding.
- [ ] Document build, tests, package layout, and integration boundary.

### Task 2: BizX Python implementation

**Files:** `BizX/python/pyproject.toml`, `BizX/python/README.md`, `BizX/python/bizx/...`, `BizX/python/tests/...`

- [ ] Add package modules for core, wallet, catalog, payments, api, and cli.
- [ ] Add pytest-free standard-library tests using `unittest`.
- [ ] Document Python runtime and package layout.

### Task 3: BizXtreme Java implementation

**Files:** `BizXtreme/java/pom.xml`, `BizXtreme/java/README.md`, `BizXtreme/java/src/main/java/...`, `BizXtreme/java/src/test/java/...`

- [ ] Add Java-native core, wallet, crypto, WebGL/Three.js boundaries, game, and API modules.
- [ ] Add unit tests for core health and wallet forwarding.
- [ ] Document packaged artifacts separately from source.

### Task 4: BizXtreme Python implementation

**Files:** `BizXtreme/python/pyproject.toml`, `BizXtreme/python/README.md`, `BizXtreme/python/bizxtreme/...`, `BizXtreme/python/tests/...`

- [ ] Add Python modules for core, wallet, crypto, WebGL, Three.js, game, and API boundaries.
- [ ] Add standard-library tests.
- [ ] Document Python integration and artifact boundaries.

### Task 5: Repository documentation synchronization

**Files:** root READMEs and docs in BizX, BizXtreme, and ChimeraIIOS.

- [ ] Update implementation matrices and language-specific documentation links.
- [ ] Add Java/Python integration guidance to Chimera II OS.
- [ ] Correct BizXtreme Node.js README if required.

### Task 6: Verification

- [ ] Fetch and inspect all newly committed files.
- [ ] Confirm no source language is mixed into Java/Python implementation trees.
- [ ] Report repository-level verification accurately; do not claim local builds unless executed.
