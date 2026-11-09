# Verified desktop and compatibility tool artifacts

The Desktop Compatibility CI and Octavian Native Desktop Suite publish Linux-host tool bundles. The bundles contain the OpenGL smoke tool, OpenCV image inspector, selected shell/desktop utilities, binary-header inspection and compatibility-runner helpers, man pages, runtime dependency reports, and an AArch64 QEMU-user smoke executable.

## Import into a local checkout

Download the latest `chimera-verified-desktop-compat-tools` or `octavian-native-desktop-components` workflow artifact ZIP, then run:

```bash
bash tools/import-verified-desktop-artifacts.sh /path/to/artifact.zip
```

The importer verifies every entry in `SHA256SUMS` before copying the files to:

```
.cache/verified-desktop-compat-tools/
```

No imported executable is run by the importer.

## Include in the next ISO build

```bash
CHIMERA_DESKTOP_COMPAT_TOOLS_DIR="$PWD/.cache/verified-desktop-compat-tools" \
  ./build-chimera-iso.sh --clean-state --storage-auto
```

The ISO builder places the verified bundle under `/payload/desktop-compat-tools/` and adds its files to the payload manifest and checksums. It does not install these host binaries into Koronos `/usr/bin` or claim that they are native Koronos executables. They are Linux-host compatibility/provider tools for the future Linux ABI/runtime path.

The bundle currently includes x86_64 Linux host executables and an AArch64 Linux smoke binary. The latter was executed with QEMU user-mode in CI; this is not a certification of all foreign architectures or Windows/macOS executable compatibility.

## Compatibility boundaries

- ELF for the host architecture may run natively on a compatible Linux host.
- Foreign Linux ELF requires the corresponding QEMU user-mode emulator and often a matching sysroot.
- Windows PE requires Windows or Wine; parsing a PE header does not make it executable.
- Mach-O requires macOS or a separately supported macOS environment; CPU emulation alone is insufficient.
- DOS MZ applications require a DOS emulator such as DOSBox.
- Compatibility mode is reported explicitly by the runner and is not represented as native execution.
