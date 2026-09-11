# Chimera II OS ISO-Tool Integration

The Chimera II OS repository can be consumed by the ISO-Tool build/image orchestrator.

## Approved consolidated pipeline

The ISO-Tool integration is committed as the approved compile → link → artifact staging → ISO mastering pipeline. It supports CMake and Visual Studio 2022/MSVC x64 Release builds, then stages generated artifacts and repository content into the image.

The pipeline explicitly reports executable, DLL, LIB and BIN artifacts as they are discovered and added, including a final artifact count. Repository source is staged under `/src`; compiled executables/binary images under `/bin`; libraries under `/lib`; and application staging under `/applications/linux` and `/applications/windows`.

## User-selected output location

Before ISO mastering, the user chooses the final save directory through the GUI. ISO-Tool shows the selected path and must not silently place the final ISO in the repository.

The default suggestion on Windows is:

```text
%USERPROFILE%\\Downloads\\Chimera-II-ISO-Tool
```

The selected directory is organized into `iso/`, `boot-images/`, `binaries/executables/`, `binaries/libraries/`, `logs/`, and `manifests/`. All generated executable, library and binary-image artifacts are retained independently as well as being staged into the ISO where appropriate.

## Dependency downloads

Dependency discovery can search trusted package-manager sources. Downloaded installers/packages are stored in:

```text
%USERPROFILE%\\Downloads\\Chimera-II-ISO-Tool\\dependencies
```

The dependency cache is independent of the final ISO destination. Before installation, the GUI displays the missing dependency, trusted source/package manager and cache destination. `Scan only` never installs; `Install missing dependencies` requires explicit authorization and never executes arbitrary remote scripts.

## ISO/media configuration

- CD and DVD media profiles.
- ISO 9660 with Joliet/Rock Ridge options.
- UDF options.
- BIOS, UEFI, or BIOS+UEFI boot configuration.
- xorriso and Oscdimg mastering backends.
- Dependency scanning and machine-readable `engine/dependencies.json`.
- Optional trusted WinGet dependency installation with explicit authorization.

## Spit Fire boot-image handling

ISO-Tool searches the repository for an assembled Spit Fire/first-stage boot binary and exports a discovered artifact when available. Generated `.bin`, `.img`, and `.efi` files are retained under `boot-images/` in the selected output directory. If no assembled artifact exists, the tool creates a clearly identified fallback container rather than representing generated placeholder data as a real bootloader.

When QEMU/OVMF is available, boot validation can save logs/evidence next to the generated artifacts. Static image generation is not treated as proof of a successful boot.

Imported boot sectors are treated as inert data and are never executed by the tooling.

## GUI and Windows toolchain

ISO-Tool provides Python/Tkinter, C# WPF, and native VC++ Win32 front ends. The native Visual Studio project embeds the Windows application icon through `ISO-Tool.rc` and exposes cumulative progress, status text and detailed live operation logging.

The native CI workflow includes a Visual Studio/MSVC x64 Release build and verifies the expected resource and executable outputs. CI status is authoritative; a repository commit does not imply that a Windows runner has already passed unless a workflow run reports success.

## Runtime resilience

ISO-Tool uses fail-forward isolation for recoverable independent job failures. Errors are logged with type/message, progress advances, and subsequent independent jobs continue. Fatal image-integrity, staging, authorization, and safety failures may still stop publication.

## Offline and network recovery

Local Chimera II OS source builds do not require Internet access. Remote source acquisition can monitor connectivity, wait for recovery, and retry network operations according to the configured retry policy. Retry activity is visible in the GUI's live operation-details pane. Dependency downloads are retained in the profile Downloads cache for repeatable offline use when the package manager supports it.

## Chimera II package/application integration

The companion Chimera II OS repository contains the unified package-source registry and application-provider metadata used by the ISO/application ecosystem. Native adapters cover Debian/Ubuntu APT, Fedora/Rocky DNF, openSUSE Zypper, Arch pacman, Alpine apk, Void XBPS, Gentoo Portage, Homebrew, Flatpak, Snap, WinGet/Microsoft Store, Chocolatey and Scoop.

The package adapter requires explicit `--yes` authorization for installation and does not execute arbitrary downloaded scripts.

## Workflow entry points

- `analyze-source` — inspect the Chimera II OS source tree.
- `build-compiled-images` — compile/assemble authorized boot, kernel and application artifacts.
- `import-boot-image` — inspect and stage a bounded boot sector or image artifact.
- `build-iso` — construct the configured Live/Install ISO or IMG.
- `validate-image` — validate the generated image and checksums.

The canonical implementation is in `amerhwitat/nlp/ISO-Tool/`.
