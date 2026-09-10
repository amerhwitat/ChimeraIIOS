# Chimera II OS — Free Hosting, Blog, Vlog & Media Distribution Plan

## Purpose

This document defines the public distribution matrix for the Chimera II OS ecosystem. The GitHub repositories and GitHub Pages site remain the canonical source of record. Copies on third-party services are mirrors or publication channels and must point back to the canonical source.

## Material to distribute

1. Chimera II OS repository and source tree.
2. Public repository portfolio and cross-repository links.
3. Developer Guide and kernel/networking documentation.
4. ISA specifications and C8192/R8192 material.
5. CPU4096 and CPU4096Simulator documentation.
6. Aurora desktop, Mobile Edition and Web UI material.
7. NLP and PDF research tooling descriptions.
8. Public screenshots, diagrams and architecture artwork.
9. Chimera II OS videos and approved media.
10. Related Library documents owned by the author, where the destination permits document uploads.

The Library contains relevant developer documentation and ISA material, including the Chimera II OS Developer Guide and IEEE-style/8192-bit ISA material. These should be published as documents or linked from the canonical repositories rather than silently converted into unrelated copies. 

## Free static hosting targets

| Service | Use | Current state | Requirement |
|---|---|---|---|
| GitHub Pages | Primary public web portal | Published | Existing GitHub authorization |
| GitLab Pages | Static mirror/documentation | Ready | User-controlled GitLab account/project authorization |
| Codeberg Pages | Open-source static mirror | Ready | User-controlled Codeberg account/repository authorization |
| Cloudflare Pages | Static deployment mirror | Ready | User-controlled Cloudflare account and GitHub/GitLab authorization |
| Other free static hosts | Additional mirrors | Candidate targets only | Each host requires its own account/deployment authorization |

GitHub Pages supports public repositories on GitHub Free. GitLab Pages provides free static hosting from repositories. Codeberg Pages provides free static project/user pages. Cloudflare Pages can deploy from GitHub or GitLab repositories. These capabilities do not by themselves authorize this session to create accounts or publish to those services.

## Free blog / publishing targets

| Service | Use | Current state |
|---|---|---|
| WordPress.com — AmerServer4 | Main technical blog/publication hub | Authorization pending |
| Blogger | Secondary technical blog | Account authorization required |
| Medium | Articles and research summaries | Account authorization required |
| Substack | Long-form research/newsletter distribution | Account authorization required |
| Other free blogging platforms | Supplemental publication | Account-specific authorization required |

Do not publish duplicate low-value copies indiscriminately. Each publication should have a distinct purpose, canonical-source links and appropriate attribution.

## Vlog / video targets

Primary approved Chimera video assets:

- `Chimera II OS Neural Simulator Execution Cycle.mp4`
- `chimera_ii_os_musical_video.mp4`

The unrelated Gaza video remains outside the Chimera publication set unless the owner explicitly requests otherwise.

Potential free/creator video channels include YouTube and other services that permit user-owned uploads. Actual uploads require authenticated account authorization. A service is marked **Published** only after a successful upload returns a retrievable public URL.

## Image / media distribution

Recommended source structure:

```text
web/assets/chimera/
  aurora/
  mobile/
  architecture/
  cpu/
  isa/
  screenshots/
```

Images should be hosted on the user's own website/repository or on an authorized image/media service. Do not mass-upload to unrelated hosts and do not use third-party hotlinks as the canonical copy.

## Library-file distribution

Relevant Library files can be used as source material for public documentation. Publication should preserve:

- original filename and version where practical;
- author attribution;
- copyright/license information;
- repository/source link;
- document provenance;
- distinction between research notes, specifications, implementation code and generated drafts.

A Library file is not considered externally published until an authenticated destination confirms the upload and provides a retrievable URL.

## Canonical links

- GitHub source of record: https://github.com/amerhwitat/ChimeraIIOS
- Public web portal: https://amerhwitat.github.io/chimera/
- Ecosystem portfolio: `docs/CHIMERA_ECOSYSTEM_PORTFOLIO.md`
- Publication registry: `docs/PUBLICATION_AND_MEDIA_DISTRIBUTION.md`

## Publication rule

This project does not claim universal publication merely because a platform supports free hosting. External publication requires an authenticated write operation and a retrievable destination URL. Platforms without a connected account remain **Ready/Pending**, not **Published**.

## Privacy and provenance

- Private repositories are excluded from public mirrors.
- Third-party code and media are not republished without applicable rights and license compliance.
- No passwords, browser credentials, API secrets or recovery codes are included in publication packages.
- Public copies should link back to the canonical Chimera II OS repository.
