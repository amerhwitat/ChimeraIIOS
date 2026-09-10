# Chimera II OS — Publication & Media Distribution Registry

## Canonical publication

- GitHub source of record: https://github.com/amerhwitat/ChimeraIIOS
- Public web portal: https://amerhwitat.github.io/chimera/
- Portfolio summary: `docs/CHIMERA_ECOSYSTEM_PORTFOLIO.md`

## Secondary publication targets

| Destination | Intended material | Status | Publication evidence |
|---|---|---|---|
| GitHub repositories | Portfolio summary, ecosystem links, documentation | Published in owned public repositories | Repository commits are the source evidence |
| GitHub Pages | Public HTML portfolio/index | Published | `amerhwitat.github.io/chimera/` |
| GitLab | Source mirror / project announcement | Not published from this session | Requires a user-controlled GitLab repository/account connection |
| Codeberg/Forgejo | Source mirror | Not published from this session | Requires user-controlled account/repository connection |
| SourceHut | Source/project publication | Not published from this session | Requires user-controlled account/project connection |
| WordPress/blog | Long-form project announcement | Pending connection | WPWriter is available but is not currently connected |
| External image hosts | Chimera II screenshots/diagrams/visual assets | Pending asset upload and host connection | No authenticated image-host write operation completed |

## Publication record rule

An entry is changed to **Published** only after a successful authenticated write and a retrievable destination URL is available. Search results, previews, generated links or intended destinations are not treated as publication evidence.

## Image distribution

The durable source for Chimera visuals is the repository/web tree. Recommended structure:

```text
web/assets/chimera/
  aurora/
  mobile/
  architecture/
  cpu/
  isa/
  screenshots/
```

External image hosts should receive copies only after the source image is identified and the account/host is authorized. Every published copy should record its canonical source path and destination URL.

## Content package

The publication package consists of:

1. Repository portfolio summary.
2. Chimera II architecture overview.
3. CPU4096 → CPU4096Simulator → C8192/R8192 lineage.
4. Aurora desktop and Mobile Edition overview.
5. Python and Java implementation tracks.
6. NLP and PDF research tooling.
7. Crypto interoperability and provenance boundary.
8. Public repository links and author bibliography.
9. Licensing/provenance statement.
10. Image/diagram manifest.

## Privacy and licensing

Private repositories are never presented as public mirrors. Third-party images and code are not republished without appropriate rights and attribution. Proprietary or confidential material remains excluded from public publication.
