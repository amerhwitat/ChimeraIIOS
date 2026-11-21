# Chimera II ecosystem deployment map

Last reviewed: 2026-10-09

This document separates the static discovery hub, browser-hosted applications, and canonical source repositories. A live web surface is not proof that the corresponding operating-system boot path or backend has been tested.

## Public surfaces

| Surface | Role | Source / verification boundary |
|---|---|---|
| [amerhwitat.github.io](https://amerhwitat.github.io/) | Static hub: hero, APPS catalog, REPOS index, Thamudic script-family references, and full-text page search via `search-index.json`. It links the public sub-apps under `apps/chimera-ii-os/web/`. | Source is [amerhwitat/amerhwitat.github.io](https://github.com/amerhwitat/amerhwitat.github.io). Check published Pages build and generated index before claiming all files are indexed. |
| [Chimera II OS hosted desktop](https://chimera-iios-120143.onhercules.app/) | Hosted React desktop SPA for Aurora/Koronos/kernel/terminal exploration. | Hosted simulation is distinct from a successful bare-metal ISO boot. |
| ThamudicScan v2.4.1 | Described project surface: Next.js scanner with image upload/camera, five-stage pipeline, five script families, sample inscriptions, field tips, and export. | The supplied host was abbreviated as `thamudicscan-...builtwithrocket.new`; the exact deployment URL must be supplied before a reliable external link can be published. The static hub's [Thamudic Scanner entry](https://amerhwitat.github.io/apps/thamudic-scanner/index.html) is the available in-repository entry point. |

## Source repositories

- [ChimeraIIOS](https://github.com/amerhwitat/ChimeraIIOS) is the canonical OS/kernel/toolchain source.
- [amerhwitat.github.io](https://github.com/amerhwitat/amerhwitat.github.io) is the static discovery hub and source for the published web sub-apps.
- [nlp](https://github.com/amerhwitat/nlp) is the source repository linked from the Thamudic scanner/epigraphy research surfaces.

## Catalog and search contract

- The static hub's `APPS` array is the application catalog and its `REPOS` array is the repository index.
- `search-index.json` supplies page title (`t`), group (`g`), description (`d`), searchable text (`x`), and path (`p`) to the hub's client-side search.
- When app pages are added or renamed, regenerate/update `search-index.json` in the same change and validate that every indexed local path exists.
- The hub's in-page ancient-script analysis is explicitly an interface demo unless a real OCR/model backend is connected. Do not label sample output as verified OCR or translation.
- Keep the established boot pipeline separate from hosted web demos: Spit Fire → Jasper/GRUB → Koronos ELF → hardware/driver initialization → scheduler/runtime loop → live/recovery/installer userspace → Aurora.

## Inventory and acceptance

Repository size/file-count figures supplied in project notes (including 2.1 GB / 3,123 files for ChimeraIIOS and 680 files for the hub) are inventory estimates, not verified by this document. To claim full catalog coverage, enumerate the actual tracked paths under `apps/chimera-ii-os/web/`, compare them with `search-index.json`, and report missing/duplicate links. Verify deployments and runtime capabilities independently from source presence.
