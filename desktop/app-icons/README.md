# Unified application icon set

This directory contains an original, scalable SVG symbol sprite and a JSON manifest for **127 unique application IDs** found in the ChimeraIIOS application catalog and the shared optional-application catalog used by ChimeraIIOS and OctavianOS.

## Use

Reference a symbol by application ID:

```html
<svg width="64" height="64" role="img" aria-label="Firefox">
  <use href="/assets/app-icons/catalog.svg#app-firefox"></use>
</svg>
```

The sprite uses generic, original icon artwork and monogram marks. It does not copy upstream product trademarks. `manifest.json` records each app's catalog provenance and explicitly marks installation status as unverified. Catalog presence must never be shown as proof that an app is installed, ported, licensed for redistribution, or launchable.

## Validation

- Unique IDs: 127
- Duplicate IDs: none (deduplicated by application ID)
- Sprite symbols: 127
- Each symbol uses a 64×64 viewBox.
