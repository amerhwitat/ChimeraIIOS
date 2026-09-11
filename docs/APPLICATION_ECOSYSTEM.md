# Chimera II application ecosystem

Chimera II uses one application manifest with provider adapters. The ISO ships the catalog, package-source registry and open-source/core tooling; proprietary applications are retrieved through their official distribution channel when licensing permits.

## Providers

- Native Chimera packages
- Debian/Ubuntu APT and `.deb`
- Fedora/RHEL/Rocky DNF/YUM and RPM
- openSUSE Zypper
- Arch pacman
- Alpine apk
- Void XBPS
- Gentoo Portage
- Homebrew
- Flatpak/Flathub
- Snap Store
- AppImage metadata
- Windows WinGet / Microsoft Store
- Windows MSIX/AppX
- Windows EXE/MSI
- Chocolatey
- Scoop
- Android APK/AAB metadata
- Web/PWA
- Apple catalog/store/web integration where supported

The authoritative source list is `package-manager/repositories.json`; it is consumed by the package-manager adapter and can also be copied into generated ISO metadata for provenance.

## Trust and licensing

Official repositories are preferred. Remote binary sources are expected to provide their native signature/integrity controls. Third-party repositories require explicit opt-in and should be pinned or otherwise constrained where the native package manager supports it.

Ubuntu's current documentation warns that third-party APT repositories introduce publisher-trust and system-integrity risks. Chimera therefore does not silently add arbitrary third-party sources. 

Windows WinGet exposes both the Microsoft Store and WinGet Community Repository as configured sources and recommends secure, trusted sources. Chocolatey's community repository is moderated but community-maintained, so Chimera records it as a distinct provider rather than treating it as equivalent to a first-party OS repository.

## ISO integration

ISO-Tool stages locally authorized open-source/free applications under:

```text
/applications/linux
/applications/windows
```

Application manifests and repository metadata may be included without redistributing software binaries whose licenses do not permit redistribution. The package manager can later retrieve the application from its configured official/provider source.

## Command adapter

Use:

```bash
python3 package-manager/chimera-pkg.py detect
python3 package-manager/chimera-pkg.py sources
python3 package-manager/chimera-pkg.py plan apt curl
python3 package-manager/chimera-pkg.py plan winget Git.Git
```

The plan operation is non-executing. Installation requires explicit `--yes` authorization.
