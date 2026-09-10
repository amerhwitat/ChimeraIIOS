# Chimera II application ecosystem

Chimera II uses one application manifest with provider adapters. The ISO ships the catalog and open-source/core tooling; proprietary applications are retrieved through their official distribution channel when licensing permits.

## Providers

- Native Chimera packages
- Linux package repositories
- Flatpak/Flathub
- AppImage
- Windows MSIX/AppX
- Windows EXE/MSI
- Android APK/AAB metadata
- Web/PWA
- Apple catalog/store/web integration where supported

Microsoft currently recommends MSIX for Store distribution, while EXE/MSI submissions are also supported. Flatpak provides distribution-agnostic runtimes and repositories. Apple's App Store distribution relies on Apple signing and App Store Connect; Chimera therefore does not claim arbitrary iOS App Store binaries can be installed on a non-Apple platform.
