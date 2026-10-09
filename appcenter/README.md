# Chimera II Application Center

The Application Center provides one catalog and provider abstraction for native Chimera packages, Linux repositories, Flatpak, AppImage, Windows MSIX/EXE/MSI, Android APK/AAB metadata, and web/PWA applications.

## Policy

The ISO contains open-source core components and metadata/source references. Proprietary binaries are not copied into the repository merely because an application is popular. The application manager opens or invokes an official distribution mechanism when a license or store policy requires it.

## Initial catalog

The initial catalog includes YouTube as a web/PWA entry, Firefox, Chromium, VLC, Telegram, Signal, Discord, Reddit, LibreOffice, GIMP and Visual Studio Code as examples. The same manifest format is intended for additional applications.

## Commands

```text
python3 appcenter/cli/chimera-appctl.py list
python3 appcenter/cli/chimera-appctl.py search media
python3 appcenter/cli/chimera-appctl.py show youtube
python3 appcenter/cli/chimera-appctl.py sources
python3 appcenter/cli/chimera-appctl.py install-plan youtube
```

`install-plan` is deliberately non-executing. An installer UI or privileged package backend must review and authorize an actual installation.

## Aurora package manager providers

Aurora's Package Manager Center calls `/usr/bin/chimera-pkg`. It detects optional system providers (APT, DNF, Pacman, Zypper, APK, Snap, Flatpak, Homebrew and Nix) and JavaScript providers (npm, Yarn, pnpm and Corepack). Yarn global commands vary by Yarn major version; Corepack is preferred for project-pinned Yarn/pnpm versions.

Useful commands:

```sh
chimera-pkg status
chimera-pkg search sqlite apt
chimera-pkg databases
```

When provider is `auto`, failed read-only package searches may retry another installed provider. Install, remove and update operations never silently switch providers. Build dependency installation is disabled by default; explicitly opt in with `./build-chimera-iso.sh --install-build-deps` to let the builder try available host package managers when required build tools are missing. This may install system packages and therefore requires root or sudo. It does not bypass Docker daemon readiness checks or run remote installer scripts.

