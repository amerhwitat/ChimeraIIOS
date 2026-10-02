# Chimera II Desktop Compatibility Matrix

## Scope

Chimera II uses Aurora as its native desktop and exposes selectable desktop personalities. Linux desktop environments may be staged as open-source packages when the target distribution supplies them. Windows and macOS are represented through compatibility/personality layers rather than redistribution of proprietary system binaries or protected artwork.

## Linux profiles

The profile catalog includes Aurora, GNOME, KDE Plasma, Xfce, Cinnamon, MATE, LXQt, LXDE, Budgie, COSMIC, Deepin, Pantheon, Enlightenment, UKUI, Trinity, Lumina, Moksha, Sway, i3, Hyprland, Openbox, IceWM and Fluxbox.

Debian's current desktop task documentation lists GNOME, Xfce, KDE Plasma, Cinnamon, MATE, LXDE and LXQt among selectable desktop environments, while Fedora documents additional spins such as Budgie, COSMIC, Sway and i3. These are used as package/profile references, not as a claim that every profile is available from every distribution. citeturn0search12turn0search19

## Windows personalities

`windows-modern` and `windows-classic` provide Chimera UI themes, shell conventions, keyboard/menu behavior and a Wine-based compatibility path for Windows applications. Windows itself uses Explorer as its standard shell and Microsoft documents custom shell replacement through Shell Launcher on supported editions. Chimera does not redistribute Windows Explorer or other Microsoft binaries. citeturn0search0turn0search2

## macOS-inspired personality

`macos-inspired` provides an independently implemented Chimera visual and interaction personality. macOS binaries, Finder, AppKit and Apple artwork are not redistributed. Apple's AppKit documentation is used as an API/interaction reference only. AppKit supplies window, menu, cursor, event, accessibility and sound concepts for native macOS applications. citeturn0search1turn0search9

## Runtime architecture

```text
Koronos
  -> Chimera graphics/input ABI
  -> Aurora compositor / Wayland
  -> desktop profile
       |-- native Aurora
       |-- Linux DE package/profile
       |-- Windows personality + Wine
       `-- macOS-inspired personality
```

Desktop selection must never become a boot-critical dependency. If a selected desktop cannot start, Chimera falls back to Aurora recovery/session selection.

## Binary policy

- Redistribute open-source Linux binaries only when their licenses and target distribution permit it.
- Prefer package-manager staging over copying arbitrary host binaries into the ISO.
- Record package name, source distribution, version and license in the generated build manifest.
- Do not copy proprietary Windows or Apple binaries into Chimera.
- Do not copy proprietary Microsoft/Apple artwork, fonts or trademarks into the runtime.
- Use compatibility layers and independently implemented themes instead.
