# Arabic Desktop and Localization

Chimera II OS now defines Arabic as a first-class `ar`/`ar-SA` locale with RTL layout semantics across the desktop compatibility layer.

## Scope

- Unicode/UTF-8 Arabic text throughout user-facing resources.
- RTL root layout for Arabic desktop sessions.
- Arabic menus, settings, system actions, diagnostics, drivers, storage and developer tools.
- Locale-aware dates, numbers and text direction must remain delegated to platform/Unicode libraries rather than hand-written shaping.
- C, C++, Rust, Python, Java, C#, Kotlin, Swift, TypeScript and Dart adapters expose the same locale contract.
- Desktop profiles cover GNOME, KDE Plasma, Xfce, Cinnamon, MATE, LXQt, classic/modern Windows and Cocoa/SwiftUI-inspired macOS layouts.

## RTL rules

Never reverse Arabic strings manually. Keep logical Unicode order and let the text/layout engine perform shaping, BiDi processing and glyph selection. Direction-sensitive UI geometry should use logical `start`/`end` semantics. Icons that encode direction may need mirrored variants; clocks, graphs, media timelines and non-directional imagery should not be mirrored.

These rules follow public platform guidance: Microsoft recommends RTL flow and flexible layout sizing for Arabic, while Apple documents automatic mirroring through standard layout systems and explicit RTL testing. GNOME, KDE Plasma, MATE and LXQt are represented as compatibility profiles rather than copied desktop implementations.

## Desktop personalities

The compatibility layer is a behavior and appearance model. It does **not** claim to reproduce proprietary Windows or macOS source code or redistribute their assets. Open-source projects remain governed by their own licenses and provenance records.

## Test matrix

At minimum test each desktop personality with:

1. `en-US` LTR.
2. `ar-SA` RTL.
3. mixed Arabic/Latin text.
4. Arabic + European numerals.
5. Arabic + file paths/URLs.
6. keyboard switching between Arabic and English.
7. long translated strings and narrow windows.
8. dialogs, menus, taskbars/panels and context menus.
9. accessibility and screen-reader labels.
10. Unicode normalization and clipboard round trips.

Sources: Microsoft globalization/RTL guidance; Apple localization/RTL guidance; GNOME, KDE Plasma, MATE and LXQt project documentation.
