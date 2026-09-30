# Chimera Game Platform

The Chimera Game Platform is the shared original-game runtime boundary for BizX and Aurora.

## Runtime layers

1. Deterministic fixed-step simulation.
2. World/terrain streaming and LOD.
3. NPC/AI, inventory, quests, dialogue and faction systems.
4. Physics, vehicles and animation.
5. Renderer adapters: OpenGL/Vulkan and optional external engine adapters.
6. Spatial audio and input.
7. Save/replay/network snapshots.
8. Storyboard and localization data.

## Original-game rule

Commercial game mechanics may inform generic system design, but proprietary code, characters, maps, dialogue, models, music, textures, voice recordings and other protected expression are not copied.

## Story data

Each original title may use:

```text
storyboards/<game>/
  synopsis.md
  characters.yaml
  world.yaml
  factions.yaml
  timeline.yaml
  chapters/
  cinematics/
  dialogue/
  quests/
```

## Aurora contract

A built game becomes visible to Aurora only after source/license validation, target compatibility validation, package checksum generation and registry publication.

## Hardware-aware launch

Aurora queries Koronos capability data for CPU architecture, thread count, RAM, GPU, VRAM, display, audio, input and graphics API support. The result selects a configuration class; it does not silently install drivers or modify hardware configuration.
