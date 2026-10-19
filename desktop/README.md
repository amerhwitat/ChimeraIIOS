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
## Cross-platform application ecosystem

desktop/application-ecosystem.json is the shared discovery and integration catalog for common Windows, Linux and macOS desktop workflows: painting/image editing, media playback and creation, office/productivity, browsers/communication, games/emulators, development tools, archives and accessibility. It records upstream project URLs, platform scope, license notes and explicit implementation states. The catalog is broad, not exhaustive, and does not claim that catalog-only or proprietary apps are bundled or runnable.

The shared Aurora/Marine preview launcher now includes usable browser-local preview apps:
- **Paint Studio** — pointer drawing, color/brush controls and PNG export.
- **Media Player** — play a user-selected audio/video file with browser-supported codecs.
- **Image Viewer** — preview a user-selected image.
- **Game Center** — playable Tic-Tac-Toe and links to game projects.
- **Text Editor** — plain-text editing and .txt export.
- **Calculator** — basic arithmetic.
- **Desktop App Catalog** — browse upstream applications, platform targets and integration status.

Run `node --check desktop/shared/desktop-parity.js` and `python3 -m unittest discover -s tests/desktop -v`.

**Important native boundary:** these built-in apps are browser-preview implementations. The catalog is not a package repository, third-party apps are not automatically installed, and a URL is not a native launch adapter. Native integration still requires target-specific packages/ports, dependency resolution, licensing and notices, MIME/open-with associations, process/session launch, sandbox/signature/update policy, accessibility, codec/graphics/input support and install/launch/quit tests. The new `application-ecosystem` acceptance gate remains `not_implemented` until retained target evidence proves those behaviors.
