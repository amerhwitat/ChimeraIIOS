# Cross-platform desktop parity implementation plan

**Status: reference inventory and engineering plan only.** This does not claim that Windows, Linux, or macOS desktops have been ported, nor that the native Aurora compositor is production-ready.

## Reference research

The inventory in `desktop/upstream_desktop_feature_matrix.json` covers Linux/BSD environments (GNOME, KDE Plasma, Xfce, Cinnamon, MATE, LXQt, LXDE, Budgie, Pantheon, COSMIC, Deepin, Enlightenment, i3, Sway, Hyprland), Windows desktop generations and WinUI patterns, and classic/current macOS/AppKit/SwiftUI patterns.

Use official project and platform sources to define user-visible behavior, not to imply source-code compatibility. For example, GNOME documents the overview, top bar, workspaces, notifications and extension model; KDE Plasma documents launchers, panels, widgets, system tray, notifications and settings; Apple's macOS HIG describes the menu bar, Dock, window management, full-screen and multi-display behavior. References:
- GNOME: https://www.gnome.org/ and https://help.gnome.org/gnome-help/shell-overview.html
- KDE Plasma: https://kde.org/plasma-desktop/
- Windows SDK: https://learn.microsoft.com/en-us/windows/win32/
- Windows App SDK / WinUI: https://github.com/microsoft/microsoft-ui-xaml
- macOS HIG: https://developer.apple.com/design/human-interface-guidelines/designing-for-macos/
- AppKit: https://developer.apple.com/documentation/appkit/
- SwiftUI: https://developer.apple.com/swiftui/

## Integration design for both OSes

Keep one shared behavior contract and separate implementations:
1. **Aurora shell contract** — session lifecycle, window manager/compositor, input/focus, launcher/search, panel/dock, notifications, workspaces/displays, settings/theme, file manager, accessibility, sound/network/power, security and crash recovery.
2. **Backend boundary** — native bare-metal compositor/display/input backend; hosted Linux/Wayland/X11 backend; Windows host integration; macOS host integration. Host APIs must be called through supported APIs; do not claim the bare-metal kernel has inherited host desktop APIs.
3. **Personality layer** — Aurora Wayland Glass as the default, Marine as the Windows-like personality, plus configurable GNOME/Plasma/traditional/macOS-inspired interaction profiles. Reuse common behavior, not copied proprietary UI assets or code.
4. **Capability detection** — each feature reports supported/unsupported/partial and a reason. A profile is not allowed to claim a capability merely because its JSON lists it.
5. **Real actions only** — launchers start real processes; task lists reflect actual windows; settings persist; file operations use actual filesystem APIs; power/network/sound controls call real services.
6. **Accessibility and localization** — keyboard navigation, focus order, scaling, contrast, reduced motion, screen-reader tree, RTL and translated strings are tested from the beginning.

## Implementation order

- **P0 foundations:** session process, display backend, window lifecycle, input routing, event loop, configuration persistence, logging and crash handling.
- **P1 usable shell:** launcher, task switcher, panels/dock, workspace management, notifications, file manager, settings and lock/logout.
- **P2 platform integrations:** Wayland/X11 hosted backends; Win32/Windows App SDK host adapter; macOS AppKit/SwiftUI host adapter. These are hosted integrations, not a claim to replace the host kernel.
- **P3 advanced behavior:** multi-display/hotplug, snapping/tiling, touch/gesture, accessibility, RTL, themes, reduced motion, app permissions, session recovery.
- **P4 release integration:** package artwork and executable assets with provenance; connect the session to the actual Live/Installer/Recovery userspace launch; run GUI smoke tests in each supported host and QEMU/physical target where applicable.

## Acceptance gate

For every capability, attach a source implementation and tests. Tests must verify real windows/processes, input/focus, persisted settings, permission failures, crash handling, display changes, accessibility and localization. Validate hosted backends separately from the bare-metal compositor. Verify the actual ISO staging and session launch path before saying Aurora is integrated.

Do not merge as production-ready or publish an OS release on the strength of a profile catalog, static mockup, web preview, successful compile, or screenshot. Both OSes must pass the same test matrix on the exact commit.

## Legal and provenance

Treat the upstream catalog as a list of references, not a license to copy. Review each repository/component's license before importing code, icons, themes, fonts, logos or other assets; preserve copyright and license notices. Microsoft and Apple APIs/design references do not grant rights to redistribute proprietary shell implementations or assets. Use original Aurora/Marine assets or separately licensed assets.

## Current result

This change adds a shared machine-readable reference inventory and a mirrored implementation/acceptance contract. It does **not** implement a full compositor, port every desktop environment, build either OS, execute desktop tests, merge changes, or publish releases. Capability entries remain `planned` until real implementation and evidence exist.
