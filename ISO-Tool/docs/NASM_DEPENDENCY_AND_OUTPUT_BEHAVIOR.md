# NASM Dependency and Output Behavior

ISO-Tool treats NASM as a build dependency when assembly sources or boot-image assembly require it.

1. Check whether NASM is already available on `PATH`.
2. If it is missing, download the trusted NASM distribution into `%USERPROFILE%\\Downloads\\Chimera-II-ISO-Tool\\dependencies\\nasm\\`.
3. Show the exact downloaded dependency folder in the UI/log immediately after download.
4. Verify the downloaded package before installation.
5. Install NASM automatically when automatic dependency installation is enabled/authorized.
6. Re-detect NASM and report the installed version/path.
7. Do not execute arbitrary downloaded scripts.

The dependency cache is retained for subsequent builds.

Before ISO mastering, ISO-Tool asks the user to select the final output directory. The selected directory contains:

- `iso/` — final ISO image(s)
- `boot-images/` — Spit Fire BIOS/UEFI and other generated boot images
- `binaries/executables/` — EXE and other executable artifacts
- `binaries/libraries/` — DLL, LIB, SO and other libraries
- `logs/` — build/dependency/mastering logs
- `manifests/` — artifact and dependency manifests

When ISO generation completes successfully, ISO-Tool opens/shows the selected destination folder and highlights the generated ISO file. The live log reports the destination directory and final ISO path.

This behavior is part of the Python/Tkinter, C# WPF and native Visual C++ ISO-Tool front ends.
