# Aurora Desktop Compatibility

Aurora now exposes one Chimera event vocabulary with native adapters for Linux, Windows and macOS. The design is based on documented platform behavior rather than copying proprietary desktop source.

## Windows

The Windows adapter models the Win32 desktop/window/message model: windows, client/non-client areas, handles, menus, keyboard accelerators, focus, pointer and system events. Microsoft documents Win32 as the native desktop API and its event/message ecosystem as the foundation for native Windows applications. citeturn0search11turn0search15

Compatibility profiles cover classic Win32 conventions through NT-era, XP, Vista/7, 8/8.1, 10, 11 and the current Windows App SDK boundary. These are behavioral profiles, not copies of Microsoft binaries.

## Linux

Aurora supports two major desktop adapter families: GTK/GDK and Qt, plus X11 and Wayland integration boundaries. GTK translates window-system input into events and propagates them through widget hierarchies; Qt represents events as QEvent objects delivered through QObject/event handling. citeturn0search5turn0search4

Profiles cover X11, GTK2/3, GTK4, Qt4/5, Qt6 and Wayland-era desktops. Legacy profiles preserve interaction conventions while the native backend remains replaceable.

## macOS

The macOS adapter models AppKit's NSApplication/NSWindow/NSView hierarchy and NSResponder event chain. AppKit handles mouse, keyboard, trackpad, touch, gestures, menus, windows, accessibility and appearance; SwiftUI can sit above the AppKit runtime boundary. citeturn0search1turn0search7

Profiles cover Classic-Mac-inspired interaction, Cocoa/AppKit, modern macOS and SwiftUI-era presentation.

## Canonical event model

`hardware/input -> native adapter -> CHM event -> focus/hit-test/gesture routing -> window/widget -> command -> application`

The schema is `desktop/event_schema.json`; profiles are `desktop/platform_profiles.json`.

## Language implementations

The same event vocabulary is exposed in C, C++, Rust, Python, Java, C#, Kotlin, Swift and TypeScript. Each language directory owns its native integration boundary while sharing the canonical schema.

## Security

Native platform code is loaded only through explicitly configured backends. Aurora does not install third-party GUI binaries, bypass OS security, or claim that a compatibility personality is the original proprietary operating system.
