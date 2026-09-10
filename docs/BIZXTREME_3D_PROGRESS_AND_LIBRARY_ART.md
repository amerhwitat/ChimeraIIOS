# BizXtreme 3D Progress and Library Art Integration

## Purpose

This document records the shared visual integration for BizXtreme and the Aurora/Chimera II OS ecosystem.

## 3D progress indicators

The game UI uses shallow extruded progress bars with a dark 3D shell, emissive fill volume, highlight strip, animated pulse, and value-driven fill geometry. The visual treatment communicates state in the same spatial language as Aurora's 3D desktop and Chimera II OS visualizations.

The canonical Three.js implementation is `BizXtreme/threejs/src/game/progress3d.js`.

## Library artwork

The selected user Library artwork is:

1. `Aurora Wayland Desktop Showcase.png` — Aurora atmosphere and loading/frontier reference.
2. `Chimera II OS Aurora Showcase.png` — Chimera technology/system-core reference.
3. `Aurora Wayland Glass Desktop.png` — glass UI and scenic environment reference.

The images were inspected from the user's Library and the runtime art direction was derived from their aurora, glass, cyan/violet, mountain, orbital-ring, and glowing-core motifs. The source Library assets remain the canonical originals.

## Cross-client contract

Unity, Three.js, Web UI, and future native clients should use stable logical asset IDs and the same progress-state vocabulary. Client-specific rendering is allowed, but the visual identity and semantic state must remain aligned.

## Performance policy

Promotional source images should not be loaded at full resolution into every gameplay scene. Runtime derivatives, mipmaps, compression, and lazy loading should be used where appropriate. Three.js provides TextureLoader/ImageLoader and texture disposal APIs for this lifecycle.

## Documentation status

This is a design/integration record. It does not claim that every Unity/native build has been compiled or that Library binary files have been uploaded into every repository.
