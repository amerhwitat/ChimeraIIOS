# Native desktop shell prototypes

`chimera-desktop-shell` is a GTK4-native Linux user-space shell client with two selectable personalities:

- `--desktop=aurora`: **Aurora Wayland Glass Desktop** presentation, with a global title bar, glass-style cards, sidebar and dock-like application grid.
- `--desktop=marine`: **Marine Desktop** presentation, with its own blue taskbar/panel visual identity.

Build on a Linux development host with GTK4 development headers:

```sh
c++ -std=c++20 -O2 $(pkg-config --cflags gtk4) desktop/native/chimera-desktop-shell.cpp \
  $(pkg-config --libs gtk4) -o chimera-desktop-shell
./chimera-desktop-shell --desktop=aurora
./chimera-desktop-shell --desktop=marine
```

The launcher uses an allowlist of fixed host commands and does not interpolate shell strings. Missing host applications are reported in the status line. The `--self-test` flag builds and presents the window, then exits for headless CI under Xvfb.

**Important runtime boundary:** this is a native GTK shell client for a Linux user-space/display server. It is not a Wayland compositor and cannot run directly on Koronos until the kernel can execute ordinary user processes and the OS has compatible graphics, input, and service APIs. The existing HTML designs remain reference prototypes; this source is a separate native implementation path, not proof that all desktop functions are complete.
