# Chimera II OS boot visual assets

The ISO builder accepts the supplied Aurora artwork and Neural Simulator MP4 as build inputs.

Expected optional source files:

- `assets/boot/chimera-intro.mp4` — the boot/installer MP4.
- `assets/boot/chimera-intro.mp4.b64` — Base64 fallback for environments where binary source assets are supplied as text.

The build converts the Aurora source artwork to `boot/visual/aurora-background.jpg`, writes a Base64 copy, stages the MP4, validates both checksums, and places them in the bootable ISO.

For an external MP4:

```bash
export CHIMERA_BOOT_VIDEO_SOURCE=/path/to/Chimera\ II\ OS\ Neural\ Simulator\ Execution\ Cycle\(1\).mp4
boot/iso/build-iso.sh
```

The MP4 is deliberately started by the native Aurora/Koronos runtime rather than GRUB. GRUB only initializes graphics and displays the JPEG background. This keeps the bootloader path deterministic while allowing the installer/desktop runtime to play the video and expose the live boot/service log.
