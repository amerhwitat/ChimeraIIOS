# Aurora `init.mp4`

`init.mp4` is the canonical Aurora initialization video asset. The repository build system generates it deterministically from the canonical Aurora artwork when the binary is not already present, then stages it at:

`/usr/share/chimera/aurora/assets/init.mp4`

The runtime uses it as the optional Aurora splash and GUI installer visual. The video is never required for BIOS/UEFI boot, recovery, or text installation.

To generate the asset locally:

```bash
bash tools/generate-aurora-media.sh
```

To use a specific source image:

```bash
CHIMERA_AURORA_SOURCE_IMAGE=/path/to/aurora-background.jpg bash tools/generate-aurora-media.sh
```
