# Native desktop shell prototypes

`chimera-desktop-shell` is a GTK4-native Linux user-space shell client with four selectable desktop personalities:

- `--desktop=aurora`: **Aurora Glass** presentation with a translucent-inspired title bar, sidebar and dock-like application grid.
- `--desktop=marine`: **Marine Blue** presentation with its blue workspace and panel identity.
- `--desktop=freexp`: **FreeXP Classic** presentation, with a classic Start menu, taskbar and DOS application shortcut.
- `--desktop=freewin11`: **FreeWin11** presentation, derived from the FreeXP profile but restyled around a modern Windows 11/12-inspired Start menu, taskbar, pinned application shortcuts and system-tray-style status area.

Build on a Linux development host with GTK4 development headers:

```sh
c++ -std=c++20 -O2 $(pkg-config --cflags gtk4) desktop/native/chimera-desktop-shell.cpp \
  $(pkg-config --libs gtk4) -o chimera-desktop-shell
./chimera-desktop-shell --desktop=freewin11
./chimera-desktop-shell --desktop=freexp
```

The launcher uses an allowlist of fixed host commands and does not interpolate shell strings. Missing host applications are reported in the status line. The `--self-test` flag builds and presents the window, then exits for headless CI under Xvfb.

**Important runtime boundary:** this is a native GTK shell client for a Linux user-space/display server. It is not a Wayland compositor and cannot run directly on Koronos until the kernel can execute ordinary user processes and the OS has compatible graphics, input, and service APIs. The FreeWin11 visual design is an original compatible shell, not a copy or redistribution of Microsoft Windows binaries or assets.
