# Portfolio 128D P2P License Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Standardize the Amer Hwitat GitHub portfolio around accurate READMEs, GNU GPLv3-or-later licensing for authored code, a common authenticated P2P interoperability layer, and the 128D multidimensional semantic model.

**Architecture:** Keep each repository and language implementation independent while interoperating through canonical JSON schemas, deterministic conformance vectors, and a transport-independent peer envelope. The 128D layer is semantic and extensible beyond 128 dimensions; P2P is opt-in, authenticated, capability-aware, replay-resistant, and never performs unsolicited scanning or remote code execution.

**Tech Stack:** C/C++, C#, F#/VB where present, Java, Node.js, Python, JavaScript/TypeScript, assembly for low-level OS components, JSON Schema, TCP/UDP/QUIC/WebSocket/WebRTC where appropriate.

**Spec:** `docs/CHIMERA_128D_P2P_INTEROPERABILITY.md`, `docs/CHIMERA_P2P_PROTOCOL.md`, and `docs/CHIMERA_128D_APPLICATION_PROFILE.md`.

## Global Constraints

- Use GNU GPL v3 or later for original project/application code unless a repository already specifies a compatible license.
- Preserve third-party licenses; do not relicense vendor/upstream code as GPL.
- Use authenticated, opt-in peer communication with identity/capability checks, sequence validation, payload hashing, replay protection, and local authorization.
- Do not add unsolicited Internet scanning, credential/private-key exchange, arbitrary executable transfer, or remote command execution.
- Embed the 128D model as a semantic state/profile layer; implementations may activate a subset or extend beyond 128 dimensions.
- Keep language-specific implementations native and interoperable through shared schemas rather than copying one language implementation into another.

---

### Task 1: Portfolio documentation and canonical contracts

**Files:**
- Modify: `README.md`
- Create: `docs/CHIMERA_128D_P2P_INTEROPERABILITY.md`
- Create: `docs/CHIMERA_PORTFOLIO_INTEGRATION_MATRIX.md`
- Create: `docs/CHIMERA_P2P_PROTOCOL.md`
- Create: `docs/CHIMERA_128D_APPLICATION_PROFILE.md`

**Interfaces:**
- Produces the canonical semantic model, P2P envelope, portfolio mapping, and implementation rules consumed by every repository.

- [ ] Write canonical architecture documents and cross-repository mappings.
- [ ] Verify all named repositories and language tracks against GitHub repository metadata before documenting them.
- [ ] Commit documentation as one reviewable unit.

### Task 2: Repository-by-repository README and license normalization

**Repositories:** `BizX`, `BizXtreme`, `CPU4096`, `CPU4096Simulator`, `PDFreaderPY`, `nlp`, `eth-key-check`, `bruteforce`, `keygen`, `test`, `general`, `VanG`, `amerhwitat.github.io`.

**Files:**
- Modify/Create: each repository `README.md`
- Create where missing: each repository `LICENSE`
- Create: each repository `docs/CHIMERA_128D_P2P_128D_INTEGRATION.md`

**Interfaces:**
- Each README accurately describes actual repository contents and points to the canonical Chimera interoperability contract.
- Each repository uses GPLv3-or-later for authored code while preserving third-party licensing.

- [ ] Inspect each repository README and top-level tree.
- [ ] Update the README with actual language/build/application scope, 128D integration, P2P integration, security boundaries, and licensing.
- [ ] Add GPLv3 license text/notice when absent.
- [ ] Add repository-specific integration documentation.
- [ ] Commit each repository independently.

### Task 3: Native language P2P adapters

**Files:** repository-specific source directories for C/C++, C#, Java, Node.js, Python, JavaScript/TypeScript; assembly only for OS/boot-level adapters.

**Interfaces:**
- Every adapter serializes/deserializes the same envelope fields: `version`, `type`, `node_id`, `sequence`, `timestamp`, `capabilities`, `object_id`, `payload_hash`, `payload`, optional `signature`.
- Every adapter exposes request/response and publish/snapshot/delta flows with local authorization.

- [ ] Add only the language implementations that match existing repository language tracks.
- [ ] Add deterministic serialization and SHA-256 payload hashing.
- [ ] Add sequence/replay validation and capability checks.
- [ ] Add loopback/local integration tests for every native adapter.
- [ ] Commit each implementation with its tests.

### Task 4: Application-specific 128D/P2P integration

**Targets:** BizX/BizXtreme, NLP/PDFreaderPY, CPU4096/CPU4096Simulator, ChimeraIIOS/keygen/test, security research repositories, and portfolio site.

- [ ] Map business/game state to multidimensional objects/events.
- [ ] Map linguistic/document knowledge to content-addressed objects with provenance.
- [ ] Map CPU/simulator state to multidimensional node/register/event state.
- [ ] Keep cryptographic research repositories limited to safe authorized test vectors and metadata exchange.
- [ ] Link all projects from the portfolio documentation.
- [ ] Add tests/conformance vectors for cross-repository envelope compatibility.

### Task 5: Verification and completion

- [ ] Re-fetch every modified README and integration document from GitHub.
- [ ] Verify every repository has the intended license state without overwriting incompatible third-party licensing.
- [ ] Validate JSON schemas and representative envelope vectors.
- [ ] Run available repository tests/builds; record failures rather than claiming success.
- [ ] Produce a final repository-by-repository change report with commit references.
