# ISO-Tool unified GUI button reference

All maintained ISO-Tool front ends use the same six feature groups and 48 feature names: Source & Repository, Toolchains, Build, ISO / Boot, Packages / Applications, and Diagnostics. The canonical list is `ISO-Tool/gui/feature_manifest.json`.

Implementations:

- Python/Tkinter: `python/launch_gui.py`
- Java/Swing: `java/src/main/java/iso/tool/Main.java` with no arguments
- C#/.NET/WPF: `dotnet/ISO-Tool/MainWindow.xaml`
- C++/Win32: `vcpp/ISO-Tool-UnifiedGui.vcxproj`

The GUIs share terminology, grouping, ordering, status reporting, and logging while retaining native platform controls. Ordinary input/runtime errors are reported in the status/log area. Missing external tools are reported rather than treated as successful operations.
