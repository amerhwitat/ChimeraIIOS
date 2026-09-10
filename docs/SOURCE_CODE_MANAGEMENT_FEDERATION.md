# Source-Code Management Federation

Chimera II OS uses Git as the portable source-history layer and treats hosting services as interchangeable forges.

## Git

Git remains the lowest common denominator:

```bash
git clone https://github.com/amerhwitat/ChimeraIIOS.git
cd ChimeraIIOS
git remote -v
git fetch --all --tags
```

A release is identified by a Git tag and commit SHA, not by a hosting site alone.

## GitHub

Primary public forge for Chimera II OS. Use repositories, issues, pull requests, Actions, releases and Pages. GitHub repository search can discover projects through names, descriptions, topics and README content. citeturn0search6

## GitLab

Planned secondary mirror for repository hosting and CI/CD. The mirror should follow the Git tag/commit produced by the canonical repository and must not become an independently diverging source of truth.

## Codeberg / Forgejo

Planned libre-software mirror. Codeberg is a community-driven, non-profit Forgejo-based platform and provides repository hosting, releases, issues, pull requests and Pages. citeturn0search4turn1search1

Codeberg's public repository workflow supports cloning and pushing existing Git repositories, which is appropriate for a mirror of the canonical Chimera tree. citeturn1search3

## SourceHut

Planned mirror for Git, patch review, mailing lists, CI and research project indexing. SourceHut currently provides hosted Git/Mercurial repositories, CI, project indexing and Pages. citeturn1search0turn1search8

## Forge-neutral policy

Every public repository should contain:

- `README.md`
- `LICENSE`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `docs/`
- provenance/third-party notices
- reproducible build instructions
- CI status and release information
- canonical/mirror relationship metadata

## Mirror configuration example

```ini
[remotes]
canonical = https://github.com/amerhwitat/ChimeraIIOS.git
gitlab = <configured GitLab mirror>
codeberg = <configured Codeberg mirror>
sourcehut = <configured SourceHut mirror>

[release]
source_of_truth = canonical
tag_policy = signed-or-checksummed
mirror_policy = exact-tag
```

The angle-bracket URLs are intentionally placeholders until the user-controlled accounts and repositories are created. Documentation must never publish a fabricated live URL.

## Research citation

For academic use, cite the immutable Git tag/commit and, where possible, archive the release with a DOI. Codeberg documents DOI-based code citation as a method for durable scientific references. citeturn1search13
