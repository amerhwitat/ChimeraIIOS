# Public Ecosystem Publication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a canonical, cross-linked portfolio summary for Amer Hwitat's public repositories and web presence, while recording external publication targets without claiming publication to services that are not connected.

**Architecture:** `ChimeraIIOS` remains the canonical source-of-record. A portfolio document contains the authoritative repository-purpose map; each public repository gets a lightweight ecosystem-link document; `amerhwitat.github.io` exposes the same portfolio on the public web. External blogs/image hosts are tracked as publication targets and are only updated through connected services with write access.

**Tech Stack:** Markdown, GitHub repositories, GitHub Pages HTML, existing Chimera documentation.

**Spec:** `docs/CHIMERA_ECOSYSTEM_INDEX.md` and the approved publication request from 2026-09-10.

## Global Constraints

- Do not expose or mirror the private `VanG` repository as public.
- Do not claim publication to external blogs/image hosts without a successful authenticated write operation.
- Preserve repository ownership, provenance, licenses, and source-of-record boundaries.
- Do not copy unrelated third-party repositories or proprietary material into the portfolio.
- Crypto documentation retains the existing prohibition on public-address-to-private-key recovery.

---

- [ ] Create the canonical portfolio summary in `ChimeraIIOS`.
- [ ] Create a common ecosystem-link document in every public owned repository.
- [ ] Update the public web index with the portfolio and repository map.
- [ ] Add the publication/asset-hosting status and external-link registry to the canonical documentation.
- [ ] Verify every created or updated GitHub file by re-fetching it.
- [ ] Report external publication limitations and connected-service next steps accurately.
