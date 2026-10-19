# Chimera II Desktop Compatibility Layer

Aurora provides a native-feeling desktop personality and event model for Linux, Windows and macOS. It separates the stable Chimera event vocabulary from platform backends.

## Desktop personalities

- `linux-gtk`: GTK/GDK-style widgets, seats, pointer/keyboard/touch/gesture propagation.
- `linux-qt`: Qt-style QObject/QEvent delivery, filters and signals.
- `windows-win32`: Win32 windows, messages, menus, accelerators, focus and pointer/keyboard input.
- `windows-modern`: WinUI/Windows App SDK compatibility boundary.
- `macos-appkit`: AppKit windows/views, responder chain, menus, trackpad/touch/gesture events.
- `macos-swiftui`: SwiftUI presentation boundary over the AppKit event/runtime model.
- `classic`: compatibility personality for older desktop conventions; behavior is emulated, not copied from proprietary binaries.

The profiles describe behavior and adapter contracts. They do not claim that Chimera can reproduce every historical OS implementation byte-for-byte.

## Event pipeline

`hardware/input → platform adapter → CHM event → focus/hit-test/gesture routing → widget/window → command/action → neural accessibility/automation hooks`

The canonical event schema is in `desktop/event_schema.json`.


## Shared desktop parity prototype

The Aurora and Marine preview pages load `desktop/shared/desktop-parity.js` for launcher search, window controls, four virtual workspaces, tiling, dock/taskbar switching, quick settings, accessibility preferences, keyboard shortcuts and notification preview. This is UI-level functionality only; `nativeSessionAdapter` remains false. See `desktop/desktop-feature-contract.json` for native integration requirements and acceptance boundaries. The pages do not implement the native compositor, process lifecycle, filesystem, networking, audio, power, sandboxing or hardware drivers.
