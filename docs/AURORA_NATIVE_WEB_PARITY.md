# Aurora Native/Web Desktop Parity

Aurora has two implementations of one desktop model:

1. **Native Aurora Wayland** — real Wayland compositor surfaces, GPU rendering, input and session management.
2. **Aurora Web Desktop** — a browser-resident desktop canvas that reproduces the same visual hierarchy and runs local applications as managed embedded windows.

## Shared model

```text
                 AURORA DESKTOP MODEL
                         |
             +-----------+-----------+
             |                       |
       Native Wayland            Web Canvas
             |                       |
       real Wayland              managed windows
       application               embedded local pages
       surfaces                  constrained frames
             |                       |
             +-----------+-----------+
                         |
                 common app registry
                 terminal profile
                 command catalog
                 manual database
                 desktop profiles
```

## Visual invariants

Both surfaces use the same:

- approved Aurora Wayland Glass background
- translucent glass surfaces
- rounded corners
- blue/purple Aurora accents
- top status bar
- left application dock
- right widget rail
- bottom application dock
- terminal typography and prompt
- application window title/action geometry

## Security invariant

Visual parity does not imply privilege parity. Browser applications cannot arbitrarily kill processes, install packages, attach debuggers, access raw devices or create unrestricted host sockets. Those actions require the authorized native/session adapter.

## Application lifecycle

`launch → create surface/window → focus → minimize/maximize → resize/move → close`

The web implementation provides the visual lifecycle; native Aurora maps the same lifecycle to Wayland surfaces.

## Background asset

Pixel identity requires the same binary artwork. The repository contracts reference `assets/aurora/aurora-wallpaper.png`. A deployment missing the canonical asset must report the missing asset rather than claim exact parity.
