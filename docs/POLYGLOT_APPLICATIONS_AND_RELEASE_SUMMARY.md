# Polyglot Applications, Apps Panel and ISO Integration

**Status:** implementation committed to the feature branch; CI and ISO acceptance pending. This document distinguishes source inventory, compilation, packaging and runtime acceptance.

## Scope

The implementation inventories first-party Python, Java and Web sources. OctavianOS also includes the integrated `vendor/chimera-ii-os/source` snapshot in its inventory and payload, while excluding nested third-party vendor trees, tests, build outputs and backups.

The generated manifest is:

`/opt/aurora/apps/polyglot/polyglot-apps.json`

The corresponding source tree is staged under:

`/opt/aurora/apps/polyglot/source-tree/`

The manifest is generated from the checked-out repository revision; source counts are not hard-coded.

## Python

- Every inventoried first-party Python source is syntax-compiled in CI with `py_compile`.
- Runnable entrypoints are distinguished from importable library/module files. A library module is not falsely treated as an application.
- PyInstaller builds a separate native Linux executable on Ubuntu and a Windows `.exe` on Windows.
- A standalone Tkinter Apps Panel is also built for each target platform.
- CLI entrypoints without a GUI receive a Tkinter launch/output wrapper. Existing modules remain source/library entries rather than fabricated standalone apps.
- Executables are written to `dist/` in the polyglot build output.

Build commands:

```bash
python3 tools/polyglot_apps.py --root . --output build/polyglot-linux --platform linux --build
python3 tools/polyglot_apps.py --root . --output build/polyglot-windows --platform windows --build
```

Windows executables must be built on Windows. Linux executables are built separately; PyInstaller is not a cross-compiler.

## Java

- Java sources are inventoried and staged with repository-relative paths.
- Configured Maven projects are built with `mvn -B package -DskipTests`.
- Resulting JARs are staged under `/opt/aurora/apps/polyglot/java/`.
- Java files outside the selected Maven project remain catalogued source files; they are not claimed to be individually compiled or runnable.

## Web

- HTML, JavaScript, TypeScript/JSX source and CSS assets are inventoried and staged.
- JavaScript files are checked with Node.js `--check` in CI.
- HTML applications remain web applications and are opened by the desktop web runtime; HTML is not mislabeled as a native binary.

## Apps Panel

The existing Aurora Optional Application Center / OctavianOS Application Center now includes a searchable Python, Java and Web inventory. The native Tkinter panel is available through the desktop launcher:

`Python, Java and Web Apps`

It lists Python modules and entrypoints, Java sources, Web sources, and any staged Windows executables. It launches Python entrypoints, opens standalone HTML files, and leaves library modules and non-standalone Java/JS/CSS files correctly marked as source-only.

## ISO packaging

The live-image builder stages:

- Python, Java and Web sources and the generated manifest;
- Linux PyInstaller artifacts under `apps/polyglot/linux/`;
- Windows PyInstaller artifacts under `apps/polyglot/windows/`;
- compiled Maven JARs under `apps/polyglot/java/`;
- the Apps Panel desktop entry and fallback Python launcher.

The live-image workflow builds the Windows artifacts on a Windows runner, downloads that artifact into the Linux ISO job, builds Linux artifacts with PyInstaller, compiles the configured Maven project, and verifies the staged source manifest against the ISO filesystem.

## Wine compatibility

Wine is optional because the 32-bit compatibility stack has a substantial dependency and ISO-size cost. To request both 32-bit and 64-bit Wine in a local ISO build:

```bash
INSTALL_WINE_COMPAT=1 sudo -E bash live-image/build.sh chimera
```

The Apps Panel launches staged Windows executables through `wine` or `wine64` when installed. Wine does not guarantee that every Windows application or hardware-dependent feature will work. Without Wine, Windows executables remain packaged but cannot be launched from Linux.

The automated ISO workflow currently stages Windows executables; it does not enable Wine by default. Enable the option only when the image-size and boot tests are acceptable.

## CI and release policy

The dedicated Polyglot workflow produces separate Linux and Windows artifacts and fails if the Apps Panel or detected Python entrypoint executables are not built. The live-image workflow then includes these artifacts and checks the ISO payload.

**Pending:** workflow completion, ISO build and checksum verification, QEMU/VMware boot, desktop GUI interaction tests, Wine launch tests (when enabled), and physical BIOS/UEFI acceptance.

A successful source build or a published CI artifact is not evidence that native Koronos userspace, Installer, Recovery, SMP, or production release gates have passed. PRs remain open and no new production release is declared by this change.
