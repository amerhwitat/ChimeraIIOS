# Aurora Emulation and Free ROM Support

Chimera II OS now has a source-first emulator registry and Aurora.Emulator window contract.

## Distribution rule
The OS may bundle emulator software and build metadata, but not commercial copyrighted ROMs or proprietary BIOS images. Libretro documents that BIOS/content files are supplied by the user and MAME documents that most ROM images are copyrighted.

The free-ROM manifest accepts public-domain, CC0, suitably licensed Creative Commons, or open-source/homebrew releases with explicit redistribution terms.

## Window and display support
Aurora.Emulator supports Wayland, X11 compatibility, DRM/KMS and headless rendering; integer/aspect-ratio scaling; fullscreen/borderless modes; VSync; shaders; screenshots; recording; controller hot-plug; and RTL/LTR UI.

## ROM workflow
1. Scan system and user ROM roots.
2. Identify the target system and compatible emulator.
3. Verify hashes and license metadata.
4. Launch a sandboxed read-only session.
5. Connect video/audio/input to Aurora.
6. Load user-owned BIOS files only from the configured BIOS directory.
