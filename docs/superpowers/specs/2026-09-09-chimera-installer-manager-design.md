# Chimera II Installer Manager Design

## Goal
Add a first-class **Chimera Installer Manager (CIM)** to Chimera II OS, Aurora Wayland Glass Desktop, and the Web UI. CIM provides a unified application catalog and capability-gated installation adapters for Chimera-native packages, Linux packages, Flatpak/AppImage-style bundles, Windows installers/packages, and user-supplied portable applications.

## Architecture
The Web UI is the presentation layer. A declarative catalog describes applications, package formats, platforms, dependencies, permissions, and backend requirements. Installation requests are sent only to an authorized native/session adapter; when no backend exists, the UI exposes catalog/documentation and a simulation/dry-run mode rather than pretending that software was installed.

Linux installation uses distro/package-manager adapters such as apt, dnf, pacman, zypper, apk, and Flatpak where available. Windows installation uses authorized adapters for winget/MSIX/AppX and user-supplied installers; arbitrary executable execution is never performed by the browser. Chimera-native packages use a future `chimera-pkg` backend contract.

## User Experience
- Installer Manager is available from Aurora dock/taskbar and All Applications.
- It is also a standalone Web UI page.
- Categories: Recommended, Installed, Linux, Windows, Chimera Native, Development, Browsers, Graphics, Multimedia, Utilities, and Security Lab.
- Search/filter by application, platform, package format, architecture, and installation backend.
- Each package shows installability, source, version/channel, dependencies, permissions, and backend state.
- Actions: Install, Remove, Update, Verify, Details, Dry Run.
- Native actions require explicit capability grants and report real command/backend results.
- Web-only mode is catalog/dry-run and clearly labeled.

## Supported package models
- Chimera package: `.c2pkg` / future `chimera-pkg` backend.
- Debian/Ubuntu: `.deb`, apt.
- Fedora/RHEL family: rpm/dnf.
- Arch: pacman.
- openSUSE: zypper.
- Alpine: apk.
- Universal Linux: Flatpak, AppImage, portable archives.
- Windows: winget, MSIX/AppX, and user-supplied MSI/EXE through an authorized Windows adapter.
- Cross-platform source/build recipes are catalog entries only until an explicit build backend is configured.

## Security and correctness
- Never claim installation success from browser-only execution.
- Native install/remove/update operations require an authorized backend and capability token/session.
- Package sources are explicit and auditable.
- Checksums/signature verification are represented in the catalog contract.
- Privileged operations are separated from the Web UI.
- Windows and Linux applications are installed into their respective OS/session backends or a VM/container/session adapter; the Web UI itself does not execute host installers.
- Dry-run is the default when no native backend is available.

## Integration
- `web/installer_manager.html` + CSS/JS provide the Aurora/Web UI.
- `web/installer_catalog.json` provides the portable catalog and backend contract.
- `web/aurora_apps.json` registers CIM.
- `web/aurora_shell.js` exposes CIM from the dock/taskbar.
- `web/installer_manager_adapter.md` documents native adapter contracts and example commands without granting browser privilege.
- CPU4096Simulator receives equivalent `public/` assets.
- Other Chimera-related repositories receive a small integration manifest pointing to the canonical installer catalog and UI contract rather than duplicated installers.

## Testing
Conformance tests validate catalog schema, platform/package coverage, backend safety states, UI registration, and dry-run behavior. Runtime installation tests must execute only inside controlled CI fixtures or explicitly configured authorized adapters.
