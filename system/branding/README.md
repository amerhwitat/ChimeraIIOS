# Chimera II OS branding and offline artwork policy

Aurora Wayland Glass is the default visual identity across the boot chain, installer, lock screen, and Aurora desktop. `CHIMERA_AURORA_ASSET` selects a replacement wallpaper at build time.

## Recursive artwork embedding

The ISO builder recursively discovers supported raster, vector, and icon artwork throughout the repository (PNG, JPEG, WebP, BMP, GIF, TIFF, SVG, AVIF, HEIC/HEIF, JPEG XL, ICO, and ICNS), preserving each source-relative path. It excludes VCS metadata and generated/dependency caches. Every discovered asset is copied into the ISO and exported root filesystem; branding consumers can use the canonical offline library:

- ISO: `/system/branding/artwork-library/`
- Root filesystem: `/usr/share/chimera/branding/artwork-library/`
- Desktop library: `/desktop/aurora/assets/library/repository-artwork/`
- Aurora branding library on ISO: `/desktop/aurora/branding/artwork-library/`
- Aurora branding library in installed rootfs: `/usr/share/chimera/aurora/branding/artwork-library/`
- Source-relative asset list: `artwork-index.txt`
- Integrity list (when `sha256sum` is available): `artwork-sha256.txt`

The generated `system/branding/chimera-background.json` declares the canonical offline library and its indexes. The same complete source-relative artwork tree, index, and SHA-256 inventory are also embedded directly under Aurora's branding namespace on the ISO and installed root filesystem. The build prefers an explicitly selected wallpaper, then the legacy session wallpaper if present, then a descriptive wallpaper/background/Aurora desktop image; generated Aurora visuals remain the fallback. A missing legacy filename is not a fatal branding error.

This embedding is offline-first: boot, installer, and desktop artwork is available from the built media without fetching remote resources. Original filenames and subdirectory structure are retained in the artwork library.

## Runtime changes

After installation, `chimera-background set IMAGE` changes runtime artwork and records the selected image in `/etc/chimera/background.conf`. Bootloader/ISO artwork is immutable after an ISO is mastered; rebuilding the ISO with `CHIMERA_AURORA_ASSET` changes GRUB/Jasper/Spit Fire/installer artwork.
