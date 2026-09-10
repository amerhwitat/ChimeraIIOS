# Chimera II OS — Open-Source Research OS Publication & Forge Federation

**Author:** Amer Hwitat  
**Project:** Chimera II OS  
**Status:** Public research/engineering project

## Purpose

Chimera II OS is published as an open research operating-system and virtual-processor ecosystem. The canonical implementation remains the GitHub repository `amerhwitat/ChimeraIIOS`; related repositories provide CPU/ISA, simulation, language, document-processing, and integration work.

The publication model is intentionally **federated** rather than vendor-locked:

- GitHub — canonical public source, issues, pull requests, releases and Actions.
- GitLab — planned mirror/secondary forge.
- Codeberg/Forgejo — planned libre-software mirror and Pages publication.
- SourceHut — planned git/patch/CI/mailing-list mirror where appropriate.
- Git — protocol and repository format used for portable synchronization.
- GitHub Pages / Codeberg Pages / SourceHut Pages — public documentation and research landing pages.

Codeberg documents public repositories, releases, issues, pull requests and Pages as first-class project infrastructure; its documentation also recommends public repositories for free-software projects. citeturn0search1turn1search1 SourceHut provides Git hosting, CI, project indexing, mailing lists, patch review and Pages, making it suitable as a complementary research forge. citeturn1search0turn1search8

## Publication rule

Only material for which Amer Hwitat/Chimera II has the right to redistribute is copied into a mirror. Third-party code remains under its original license and is referenced through provenance records. Historical, proprietary or copyrighted material is not silently republished as Chimera source.

## Canonical repository family

| Repository | Role | Current GitHub visibility |
|---|---|---|
| `ChimeraIIOS` | Canonical OS | Public |
| `CPU4096` | Wide-register CPU research | Public |
| `CPU4096Simulator` | CPU simulation | Public |
| `general` | Mobile/embedded integration | Public |
| `nlp` | NLP research | Public |
| `PDFreaderPY` | PDF/document research | Public |
| `bruteforce` | Algorithm/security research | Public |
| `keygen` | Key-generation research | Public |
| `eth-key-check` | Ethereum/key analysis | Public |
| `BizX` | Related software research | Public |
| `BizXtreme` | Related software research | Public |
| `test` | Integration/test/web research | Public |
| `amerhwitat.github.io` | Public research web surface | Public |
| `VanG` | Existing repository | Private; requires owner-controlled visibility change before mirroring |

The current GitHub account inventory was checked during this publication pass. GitHub supports repository search by name, description, topics and README, so descriptive READMEs and stable public URLs are part of the discoverability strategy. citeturn0search6

## Search-engine discoverability

The project now maintains:

- `web/robots.txt`
- `web/sitemap.xml`
- descriptive HTML metadata
- a public research index
- stable documentation URLs
- repository-to-repository cross-links
- an author bibliography page
- explicit project keywords: `Chimera II OS`, `Koronos`, `Aurora`, `R8192`, `C8192`, `RegisterN`, `128D`, `operating system research`, `open source OS`, `Wayland`, `mobile OS`, `virtual processor`, `research operating system`.

Search engines cannot be forced to index a page. The correct strategy is to make the material public, crawlable, internally linked, stable, descriptive, and free of accidental `noindex` directives. Search-engine discovery remains subject to each engine's crawl and ranking policies.

## Scientific/research citation

For archival research, release tags should be paired with a persistent DOI where available. Codeberg's documentation specifically describes DOI assignment as a way to make a particular code version citable over time. citeturn1search13

Recommended citation pattern:

> Hwitat, Amer. *Chimera II OS: Open Research Operating-System and Virtual-Processor Ecosystem*. Public source repository and research documentation, 2026.

## Mirror synchronization

The canonical Git repository is the source of truth. Mirrors should be updated from Git tags rather than independently edited.

```bash
git clone https://github.com/amerhwitat/ChimeraIIOS.git
cd ChimeraIIOS
git remote add gitlab <GitLab mirror URL>
git remote add codeberg <Codeberg mirror URL>
git remote add sourcehut <SourceHut mirror URL>
git fetch --all --tags
# Review and push the signed release tag to each configured mirror.
git push gitlab main --tags
git push codeberg main --tags
git push sourcehut main --tags
```

Mirror URLs are intentionally placeholders until the corresponding accounts/repositories exist; no nonexistent URL is claimed as a live mirror.

## Open-source hosting references

- GitHub: public source, repository search, Actions and releases.
- GitLab: secondary forge and CI mirror target.
- Codeberg: libre Forgejo-based forge, repository hosting and Pages. citeturn0search4turn1search1
- SourceHut: Git/Mercurial, CI, project index, patch review, mailing lists and Pages. citeturn1search0turn1search2

## Security

Secrets, private credentials, signing keys, API keys, private user files and device certificates are never placed in public repositories. Public research documentation describes interfaces and reproducible procedures, not secrets.
