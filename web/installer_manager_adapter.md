# Chimera Installer Manager — Native Adapter Contract

CIM separates the Web UI from privileged platform operations.

## Request

`POST /api/installer`

```json
{"action":"install","app_id":"firefox","mode":"native"}
```

Supported actions: `install`, `remove`, `update`, `verify`, `dry-run`.

## Response

```json
{"ok":true,"backend":"linux-package-manager","operation":"install","package_manager":"apt","message":"completed","installed_version":"unknown"}
```

## Linux adapters

- Debian/Ubuntu: apt / deb
- Fedora/RHEL family: dnf / rpm
- Arch family: pacman
- openSUSE: zypper
- Alpine: apk
- Universal Linux: Flatpak and AppImage/portable bundle adapters

## Windows adapters

- winget for supported package identities
- MSIX/AppX through a Windows session adapter
- MSI/EXE through a local authorized installer service

## Chimera adapter

The future `chimera-pkg` backend owns installation of `.c2pkg` packages and integrates with Koronos package state.

## Safety contract

A static Web UI never executes host package-manager commands. If `/api/installer` is unavailable, CIM reports `backend-unavailable` and offers a dry run. Privileged actions require an authorized local/session backend and should return an auditable operation result. Package signatures/checksums should be verified by the backend before committing an installation.
