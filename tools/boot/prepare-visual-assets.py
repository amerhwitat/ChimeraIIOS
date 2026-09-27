#!/usr/bin/env python3
"""Prepare Aurora boot artwork/video resources for the ISO and runtime.

The source artwork may be PNG/JPEG or SVG. The build always creates a JPEG
and a Base64 copy so early/native components do not need the original source
file. SVG artwork is rasterized at build time with CairoSVG when available,
with ImageMagick as a fallback. The video is copied into the boot resource
directory and can alternatively be supplied as a pre-encoded Base64 file.
GRUB itself is never asked to decode/play MP4.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_b64(path: Path, out: Path) -> None:
    out.write_text(base64.b64encode(path.read_bytes()).decode("ascii"), encoding="ascii")


def rasterize_svg(source: Path, output_png: Path) -> None:
    """Rasterize SVG to PNG using CairoSVG, then ImageMagick as fallback."""
    output_png.parent.mkdir(parents=True, exist_ok=True)

    try:
        import cairosvg  # type: ignore
    except ImportError:
        cairosvg = None

    if cairosvg is not None:
        try:
            cairosvg.svg2png(url=str(source), write_to=str(output_png))
            return
        except Exception as exc:
            cairo_error = str(exc)
    else:
        cairo_error = "CairoSVG is not installed"

    convert = shutil.which("magick") or shutil.which("convert")
    if convert:
        result = subprocess.run(
            [convert, "-background", "none", str(source), str(output_png)],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0 and output_png.is_file() and output_png.stat().st_size:
            return
        imagemagick_error = result.stderr.strip() or result.stdout.strip()
    else:
        imagemagick_error = "ImageMagick (magick/convert) is not installed"

    raise SystemExit(
        "Unable to rasterize Aurora SVG. Install python3-cairosvg or ImageMagick. "
        f"CairoSVG: {cairo_error}; ImageMagick: {imagemagick_error}"
    )


def make_jpeg(source: Path, output: Path) -> None:
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Pillow is required to convert Aurora artwork to JPEG") from exc

    output.parent.mkdir(parents=True, exist_ok=True)

    if source.suffix.lower() == ".svg":
        with tempfile.TemporaryDirectory(prefix="chimera-aurora-") as tmp:
            png = Path(tmp) / "aurora-rasterized.png"
            rasterize_svg(source, png)
            image = Image.open(png).convert("RGB")
            image.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
            image.save(output, "JPEG", quality=82, optimize=True, progressive=True)
    else:
        image = Image.open(source).convert("RGB")
        image.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
        image.save(output, "JPEG", quality=82, optimize=True, progressive=True)


def materialize_video(video: Path | None, embedded: Path | None, output: Path) -> None:
    if video and video.is_file():
        shutil.copy2(video, output)
    elif embedded and embedded.is_file():
        output.write_bytes(base64.b64decode(embedded.read_text(encoding="ascii")))
    else:
        raise SystemExit(
            "Chimera boot video is required. Pass --video <MP4> or provide "
            "assets/boot/chimera-intro.mp4.b64."
        )


def validate_video(path: Path) -> None:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return
    result = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=codec_name,width,height", "-of", "json", str(path)],
        text=True, capture_output=True, check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"Invalid Chimera boot video: {result.stderr.strip()}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source-png", type=Path, default=None)
    p.add_argument("--background", type=Path, default=None)
    p.add_argument("--video", type=Path, default=None)
    p.add_argument("--embedded-video", type=Path, default=None)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    a = p.parse_args()

    out = a.output_dir
    out.mkdir(parents=True, exist_ok=True)
    background = a.background or a.source_png
    if background is None or not background.is_file():
        raise SystemExit("Aurora background source is required (--background/--source-png)")

    jpg = out / "aurora-background.jpg"
    make_jpeg(background, jpg)
    write_b64(jpg, out / "aurora-background.jpg.b64")

    video = out / "chimera-intro.mp4"
    materialize_video(a.video, a.embedded_video, video)
    validate_video(video)

    manifest = {
        "schema": "chimera.boot.visual.v1",
        "background": {
            "source": str(background),
            "path": str(jpg.name),
            "sha256": sha256(jpg),
            "base64": "aurora-background.jpg.b64",
        },
        "video": {"path": str(video.name), "sha256": sha256(video), "autostart": True},
        "runtime_log": "/run/chimera/boot.log",
    }
    a.manifest.parent.mkdir(parents=True, exist_ok=True)
    a.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"[AURORA] staged background: {jpg}")
    print(f"[AURORA] staged boot video: {video}")
    print(f"[AURORA] visual manifest: {a.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
