# AuroraDesktop UE5 integration

Optional Unreal Engine 5 front-end for the Aurora visual model.

## Included

- Runtime UE5 module manifest and `Build.cs`.
- UMG/Slate-compatible UI manager boundary.
- Linux-only Wayland client bridge guarded by `AURORA_USE_WAYLAND`.
- Reusable frosted-glass HLSL/USF shader.

## Intended layout

Create project assets in the consuming UE5 project:

```text
Content/Aurora/Widgets/
  WBP_AuroraPanel
  WBP_AuroraLauncher
  WBP_AuroraDock
```

Use the plugin for UI composition while keeping the native compositor implementation in `desktop/aurora/`. Do not copy native Wayland server internals into UE5.

## Performance

Use Slate for high-frequency controls, UMG for composition, render targets for dynamic surfaces, and GPU materials for blur/post-processing. Reuse textures and avoid per-frame UObject allocation.

## Linux

Install the development package providing `wayland-client` before building the Linux target. The core Chimera CMake build does not require UE5 or Wayland.
