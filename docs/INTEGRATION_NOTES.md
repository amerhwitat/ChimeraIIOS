# Integration Notes

## Scope

This repository consolidates the Chimera II OS research material available in the project workspace. It intentionally distinguishes source prototypes from future production implementations.

## Layers

1. Firmware/boot: Spit Fire and Jasper.
2. Kernel: Koronos scheduler and future MM/IPC/driver layers.
3. Services: Kore orchestration, Spotnik networking, Nucleus data, Hive registry.
4. Desktop: Aurora Wayland compositor and Vulkan/OpenGL rendering research.
5. Virtual architecture: RegisterN, R8192/C8192 and host emulation.
6. Intelligence/research: 128D, neural, observer and simulation concepts.

## Important engineering caveat

Several historical source blocks are incomplete by design or depend on APIs not yet present in this consolidation. They are retained as research artifacts rather than silently rewritten into an apparently complete operating system.

## Build baseline

The root CMake project currently targets the host-side C simulator and its unit test. Aurora, boot and other subsystems are intentionally not forced into the minimal host build because they require platform-specific dependencies or future interfaces.
