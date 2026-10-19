# Chimera II Application Center

The Application Center provides one catalog and provider abstraction for native Chimera packages, Linux repositories, Flatpak, AppImage, Windows MSIX/EXE/MSI, Android APK/AAB metadata, and web/PWA applications.

## Cross-platform desktop inventory

The expanded [application catalog](catalog/apps.json) covers common desktop workflows across graphics/paint, photo editing, 3D creation, media playback and production, office/documents, communications, security, networking, engineering/CAD, games, emulation, development and utilities. It includes open-source candidates such as Pinta, Krita, Inkscape, Blender, OBS Studio, Audacity, Kdenlive, Shotcut, HandBrake, FreeCAD, KiCad, Godot, RetroArch, SuperTuxKart and Xonotic.

**Cataloged does not mean installed, bundled, ported, or verified.** Added entries use `availability: catalog-only` until packaging, license/provenance review, dependency resolution, target-specific build and actual launch tests are complete. Host versions of Windows/macOS/Linux applications are not automatically runnable on the bare-metal Chimera kernel. Use official providers or explicitly identified web, VM, emulation, or compatibility routes where appropriate.

## Policy

The ISO contains open-source core components and metadata/source references. Proprietary binaries are not copied into the repository merely because an application is popular. The application manager opens or invokes an official distribution mechanism when a license or store policy requires it. Untrusted post-install scripts are not run implicitly.

## Commands

```text
python3 appcenter/cli/chimera-appctl.py validate
python3 appcenter/cli/chimera-appctl.py list
python3 appcenter/cli/chimera-appctl.py categories --count
python3 appcenter/cli/chimera-appctl.py search media
python3 appcenter/cli/chimera-appctl.py show youtube
python3 appcenter/cli/chimera-appctl.py sources
python3 appcenter/cli/chimera-appctl.py install-plan youtube
```

`validate` checks unique IDs, required metadata, registered provider IDs, HTTPS URLs and declared verification states. The Aurora Repository Application Center now reads this catalog for search/category discovery and only opens verified HTTPS project websites; it does not run installers. `install-plan` is deliberately non-executing. An installer UI or privileged package backend must review and authorize an actual installation.

## Aurora package manager providers

Aurora's Package Manager Center calls `/usr/bin/chimera-pkg`. It detects optional system providers (APT, DNF, Pacman, Zypper, APK, Snap, Flatpak, Homebrew and Nix) and JavaScript providers (npm, Yarn, pnpm and Corepack). Yarn global commands vary by Yarn major version; Corepack is preferred for project-pinned Yarn/pnpm versions.

Useful commands:

```sh
chimera-pkg status
chimera-pkg search sqlite apt
chimera-pkg databases
```

When provider is `auto`, failed read-only package searches may retry another installed provider. Install, remove and update operations never silently switch providers. Build dependency installation is disabled by default; explicitly opt in with `./build-chimera-iso.sh --install-build-deps` to let the builder try available host package managers when required build tools are missing. This may install system packages and therefore requires root or sudo. It does not bypass Docker daemon readiness checks or run remote installer scripts.
