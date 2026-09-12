# Build Automation

Cross-platform entry points:

- Windows CMD: `build-tools\build.bat`
- PowerShell: `powershell -ExecutionPolicy Bypass -File build-tools\build.ps1`
- Linux/macOS: `./build-tools/build.sh`
- Dry run: add `--dry-run`.
- Python/PyInstaller: `--only python --onefile`
- Java: `--only java`
- Node/web: `--only node`
- C/C++/CMake/Make/.NET: `--only native`
- SQL inventory: `--only sql`

The runner detects the actual source tree, streams compiler/linker/package output, preserves exit codes, and writes artifacts under `build/artifacts`. PyInstaller packaging is target-native; do not cross-build Windows/Linux/macOS executables. Database credentials belong in environment variables, never in source control.
