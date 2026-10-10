# Aurora Desktop

Aurora is the Chimera II graphical environment and Wayland compositor research layer. It targets a polished contemporary desktop workflow while keeping compositor, toolkit and kernel responsibilities separated.

## Design

- Wayland compositor architecture
- Vulkan/OpenGL renderer paths
- DRM/KMS or equivalent display backend
- Damage tracking and frame pacing
- Explicit synchronization and presentation timing research
- Arabic/English shaping and input-method targets
- Optional 3D effects with capability-based fallback
- Theme concepts include Chimera and contemporary desktop conventions

The current repository material is a research/prototype implementation, not a production-ready compositor.

## Hosted Edition integration

When Aurora is launched as a user-space desktop on a supported 64-bit host, the portable host bridge exposes host/ISA information and delegates file/URL opening to the native desktop:

```sh
chimera-hosted desktop-info
chimera-hosted isa
chimera-hosted open PATH_OR_URL
```

This is an integration boundary for launchers and file associations, not a claim that the Wayland compositor itself is already portable to Windows and macOS. See [Hosted Edition design](../../docs/hosted-edition.md).
