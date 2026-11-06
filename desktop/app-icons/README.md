# Unified application icon set

This directory contains an original SVG symbol sprite and JSON manifest for catalogued applications plus Aurora's built-in desktop shortcuts.

## Use

```html
<svg width="64" height="64" role="img" aria-label="Terminal">
  <use href="../app-icons/catalog.svg#app-terminal"></use>
</svg>
```

The desktop shell uses the same sprite for its default shortcuts. Generic original artwork and monograms are used rather than copied upstream logos. The manifest distinguishes catalog entries from native shell shortcuts and records installation status as unverified for external applications.

- 133 symbols total.
- One 64×64 viewBox per symbol.
- App catalog presence does not imply installation, porting, redistribution rights, or launchability.
