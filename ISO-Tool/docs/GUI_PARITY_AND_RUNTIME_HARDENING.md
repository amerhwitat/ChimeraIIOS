# ISO-Tool GUI parity and runtime hardening

The ISO-Tool GUI contract is shared by Python/Tkinter, Java/Swing, C#/.NET/WPF, and C++/Win32. The canonical feature list is `ISO-Tool/gui/feature_manifest.json`.

Each implementation presents the same six groups: Source & Repository, Toolchains, Build, ISO / Boot, Packages / Applications, and Diagnostics. The native toolkit may differ, but title, section order, feature names, status reporting, and logging vocabulary remain consistent.

Runtime failures are reported in the GUI instead of terminating the front end for ordinary user/input errors. Long-running Python work uses worker threads. Toolchain actions remain explicit and do not silently execute downloaded scripts.

NASM and GCC bootstrap behavior remains environment-dependent. The repository contains the bootstrap mechanisms and verification paths; it does not claim that a user's Windows workstation has already built those toolchains.
