# Aurora Wayland Glass Wallpaper Manager

Aurora supports importing high-resolution images and using them as desktop backgrounds across Aurora and compatible desktop personalities.

## Import

Supported image families include PNG, JPEG, WebP, AVIF, TIFF and BMP. Imported images are inspected for dimensions, orientation and color metadata before entering the wallpaper library. Originals are retained and image files are never treated as executable content.

The default quality target is a 3840-pixel long edge, while larger source images remain available at their original resolution.

## Presentation

Aurora selects the appropriate output-aware buffer scale and can display a wallpaper as fill, fit, crop, tile, center, span, or independently per monitor/output. Multi-monitor and per-workspace policies are supported.

Where the compositor provides suitable protocol support, Aurora can use native wallpaper interfaces. Current Wayland ecosystems include desktop-shell/background mechanisms and compositor-specific wallpaper protocols; these are treated as optional adapters rather than mandatory dependencies. The Weston desktop-shell protocol explicitly defines a background surface, while Treeland exposes a wallpaper manager for an output. citeturn0search2turn0search7

High-resolution output scaling is aligned with Wayland's buffer-scale model, allowing clients to provide higher-resolution buffers for high-DPI outputs. citeturn0search10

## Color and HDR

Aurora's wallpaper pipeline can retain color profiles and expose color-management metadata to compositors supporting the relevant Wayland protocols. Wayland's color-management protocol supports explicit image descriptions including SDR/HDR colorimetry and rendering intent. citeturn0search5

## Timed backgrounds

Users can schedule changes by:

- fixed interval
- clock time
- sunrise/sunset
- login
- workspace change
- manual selection

The scheduler avoids immediate repeats and can pause rotation on battery or metered-network conditions.

## Other desktop personalities

Aurora uses adapters for Linux Wayland/X11, Windows and macOS. The adapter model preserves each host desktop's native semantics instead of pretending all desktops expose the same wallpaper API.

## Safety

Remote wallpaper sources are opt-in. Downloads are policy-controlled, metadata can record source/license information, image decoding is sandboxable, and imported images are never executed as programs.
