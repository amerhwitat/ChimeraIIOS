# Chimera Package Manager

`chimera-pkg` provides one Brew-like command surface over platform-specific package providers.

## Commands

```text
chimera-pkg sources
chimera-pkg search <query>
chimera-pkg install <package> --source linux|windows|macos
```

## Provider model

- Linux: apt/dnf discovery where available; additional adapters can target pacman, zypper, apk and Nix.
- Windows: WinGet/Microsoft Store/MSIX provider boundary.
- macOS: Homebrew-compatible provider plus signed App Store/distribution boundary.
- Chimera repositories: native Chimera packages with signed manifests.

The OS must not pretend that Microsoft Store or Apple App Store packages can be installed universally. Store installation remains subject to OS APIs, signing, licensing, authentication, architecture and regional/platform restrictions. Windows Store supports MSIX and other distribution paths; Apple provides App Store Connect APIs and platform-specific distribution mechanisms.

## Security

Package metadata is separated from executable payloads. Installation requires signature verification, dependency resolution, explicit user authorization, sandbox/policy checks and a rollback point. Automatic installation is disabled by default.
