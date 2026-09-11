# Chimera II OS Package Management and Repository Registry

Chimera II OS now exposes a unified package-manager adapter while preserving the native package manager for each host/distribution.

## Supported package families

| Family | Adapter |
|---|---|
| Debian/Ubuntu `.deb` | `apt`, `apt-get`, `dpkg` |
| Fedora/RHEL/Rocky RPM | `dnf`, `yum` |
| openSUSE | `zypper` |
| Arch | `pacman` |
| Alpine | `apk` |
| Void | `xbps-install` |
| Gentoo | `emerge` |
| Homebrew | `brew` |
| Flatpak | `flatpak` |
| Snap | `snap` |
| Windows | `winget`, Microsoft Store source, Chocolatey, Scoop |
| Experimental compatibility | `fnd` |

The `fnd` entry is retained as a compatibility hook because the requested Chimera command vocabulary includes `fnd`; it is not claimed to be a universal Linux package manager.

## Repository registry

`package-manager/repositories.json` stores the repository endpoints and package formats used by the Chimera application/package layer. Official repositories are preferred and HTTPS is required by policy. Remote binary repositories are expected to provide their own signature/integrity mechanisms.

Examples include Debian's CDN-backed archive, Ubuntu archives/security, Fedora/Rocky/openSUSE RPM sources, Arch mirrors, Alpine repositories, Void repositories, Homebrew, Flathub, Snap Store, Microsoft Store/WinGet, Chocolatey and Scoop.

Debian documents `deb.debian.org` and its mirror architecture; APT obtains package metadata from configured sources. citeturn1search1turn1search3turn1search7

Ubuntu documents APT as the preferred interface for Debian packages, with `apt-get` appropriate for scripts and `.deb` files installable through `dpkg` or APT. citeturn2search0turn2search1

Arch's official repositories are maintained and consumed through pacman. citeturn0search2 Alpine defines repositories through `/etc/apk/repositories` and verifies package/index integrity. citeturn1search2turn1search4 Void requires signed remote repositories. citeturn1search0turn1search5

## Windows sources

WinGet supports the Microsoft Store (`msstore`) and WinGet Community Repository sources and allows source management through `winget source`. Microsoft explicitly recommends secure, trusted sources. citeturn0search1

Chocolatey maintains a moderated community repository, but its documentation also warns that community packages are community-maintained and not vendor-supported. Chimera therefore records Chocolatey as an explicit provider rather than silently treating it as equivalent to an OS-trusted repository. citeturn0search0turn0search6

## Usage

```bash
python3 package-manager/chimera-pkg.py detect
python3 package-manager/chimera-pkg.py sources
python3 package-manager/chimera-pkg.py plan apt curl
python3 package-manager/chimera-pkg.py plan winget Git.Git
python3 package-manager/chimera-pkg.py install apt curl --yes
```

Installation is deliberately opt-in. `plan` never executes a package command. `install` requires `--yes`.

## Security model

1. Prefer official distribution repositories.
2. Require HTTPS for configured remote sources.
3. Preserve package-manager signature verification.
4. Never execute arbitrary downloaded shell/PowerShell scripts as a package-install shortcut.
5. Record provider, package manager, source and requested package in install plans.
6. Keep third-party repositories explicitly distinguishable.
7. Do not redistribute proprietary applications merely because a store exposes a public catalog entry.

Ubuntu's third-party repository guidance specifically warns about publisher trust, repository compromise and system-integrity risks; Chimera follows that principle by requiring explicit opt-in for non-official sources. citeturn2search2
