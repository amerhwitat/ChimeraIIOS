#!/usr/bin/env python3
"""Generate offline CSS data-URI wallpapers from exact checked-in JPEG bytes."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from pathlib import Path

EXPECTED = {
    "aurora-and-mountain.jpg": {
        "id": "chimera-aurora-mountain",
        "selector": ".aurora-wallpaper--default",
        "width": 2048,
        "height": 1152,
        "background": "#07121c",
    },
    "octavian-marine-dual-brand.jpg": {
        "id": "octavian-marine-dual-brand",
        "selector": ".marine-wallpaper--default",
        "width": 1672,
        "height": 941,
        "background": "#070914",
    },
}

# Exact JPEGs uploaded to the conversation Library on 2026-10-25. These are
# dual-brand celestial/infinity and eagle/chimera concepts, not synthesized
# replacements. Copy the originals byte-for-byte into the source asset folder
# before invoking --session-branding.
SESSION_BRANDING = {
    "Duck-ai-image-2026-10-18-07-06(1).jpeg": {
        "id": "octavian-chimera-celestial-brand",
        "selector": ".dual-os-brand-wallpaper--celestial",
        "width": 1672,
        "height": 941,
        "background": "#050711",
        "expected_sha256": "a4004733cae6fb06c89d6d7e3dedf4e0190de512f7535613d51789397f0a246e",
    },
    "Duck-ai-image-2026-10-18-06-36.jpeg": {
        "id": "octavian-chimera-beast-brand",
        "selector": ".dual-os-brand-wallpaper--beast",
        "width": 1672,
        "height": 941,
        "background": "#050711",
        "expected_sha256": "049e64ef31b6506816ca32956bc439e87b32abadb96c8f56160f401e578953e4",
    },
}


def jpeg_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 4 or data[:2] != b"\xff\xd8" or data[-2:] != b"\xff\xd9":
        raise ValueError("not a complete JPEG stream (SOI/EOI markers missing)")
    i = 2
    sof = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while i < len(data) - 4:
        if data[i] != 0xFF:
            i += 1
            continue
        while i < len(data) and data[i] == 0xFF:
            i += 1
        if i >= len(data):
            break
        marker = data[i]
        i += 1
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7 or marker == 0x01:
            continue
        if i + 2 > len(data):
            break
        seg_len = int.from_bytes(data[i:i + 2], "big")
        if seg_len < 2 or i + seg_len > len(data):
            raise ValueError("invalid JPEG segment length")
        if marker in sof:
            if seg_len < 8:
                raise ValueError("short JPEG frame header")
            height = int.from_bytes(data[i + 3:i + 5], "big")
            width = int.from_bytes(data[i + 5:i + 7], "big")
            if width <= 0 or height <= 0:
                raise ValueError("invalid JPEG dimensions")
            return width, height
        i += seg_len
    raise ValueError("JPEG frame dimensions were not found")


def image_dimensions(data: bytes, mime_type: str) -> tuple[int, int]:
    if mime_type == "image/jpeg":
        return jpeg_dimensions(data)
    if mime_type == "image/png":
        if len(data) < 24 or data[:8] != bytes.fromhex("89504e470d0a1a0a") or data[12:16] != b"IHDR":
            raise ValueError("not a valid PNG stream (signature/IHDR missing)")
        width = int.from_bytes(data[16:20], "big")
        height = int.from_bytes(data[20:24], "big")
        if width <= 0 or height <= 0:
            raise ValueError("invalid PNG dimensions")
        return width, height
    raise ValueError(f"unsupported wallpaper MIME type: {mime_type}")


def _entry(path: Path, filename: str, spec: dict) -> tuple[str, dict]:
    source_file = spec.get("source_file", filename)
    if not path.is_file():
        raise FileNotFoundError(f"required wallpaper artwork is missing: {path}")
    raw = path.read_bytes()
    mime_type = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    width, height = image_dimensions(raw, mime_type)
    expected_width, expected_height = spec.get("width"), spec.get("height")
    if expected_width is not None and expected_height is not None and (width, height) != (expected_width, expected_height):
        raise ValueError(f"{filename}: expected {expected_width}x{expected_height}, got {width}x{height}")
    digest = hashlib.sha256(raw).hexdigest()
    expected_digest = spec.get("expected_sha256")
    if expected_digest and digest != expected_digest:
        raise ValueError(f"{filename}: SHA-256 mismatch; refusing to embed non-original session artwork")
    encoded = base64.b64encode(raw).decode("ascii")
    if not re.fullmatch(r"[A-Za-z0-9+/]*={0,2}", encoded):
        raise ValueError(f"{filename}: Base64 encoder produced invalid output")
    data_uri_prefix = f"data:{mime_type};base64,"
    css_rule = f'{spec["selector"]} {{ background-image: url("{data_uri_prefix}{encoded}"); }}'
    metadata = {
        "id": spec["id"], "file": source_file, "role": filename, "mime_type": mime_type,
        "width": width, "height": height, "bytes": len(raw),
        "sha256": digest, "data_uri_prefix": data_uri_prefix, "embedded": True,
        "offline": True, "fit": "cover", "dark_fallback": spec["background"],
        "related_artwork_fallback": bool(spec.get("related_artwork_fallback", False)),
    }
    return css_rule, metadata


def _generate(source_dir: Path, css_path: Path, manifest_path: Path, specs: dict, schema: str) -> dict:
    css = [
        "/* Generated by tools/wallpapers/embed_wallpapers.py; do not hand-edit. */",
        "/* Data URIs preserve original JPEG bytes for offline startup. */",
        "body { background-color: #080b12; }",
        ".aurora-wallpaper--default, .marine-wallpaper--default,",
        ".dual-os-brand-wallpaper--celestial, .dual-os-brand-wallpaper--beast {",
        "  background-position: center center; background-repeat: no-repeat; background-size: cover;",
        "}",
        "",
    ]
    entries = []
    for filename, spec in specs.items():
        source_file = spec.get("source_file", filename)
        rule, metadata = _entry(source_dir / source_file, filename, spec)
        css.append(rule)
        entries.append(metadata)
    css_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    css_path.write_text("\n".join(css) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps({
        "schema": schema,
        "source": "original JPEG bytes; no network, resizing, or re-encoding",
        "wallpapers": entries,
    }, indent=2) + "\n", encoding="utf-8")
    return {"css": str(css_path), "manifest": str(manifest_path), "wallpapers": entries}


RELATED_ARTWORK = {
    "aurora-and-mountain.jpg": (
        "Aurora Wayland Desktop - boot background.jpg",
        "Aurora-Wayland-Glass-Desktop.png(1).jpg",
        "Aurora-Wayland-Glass-Desktop.png",
        "Aurora Wayland Desktop Showcase.png",
    ),
    "octavian-marine-dual-brand.jpg": (
        "Aurora Wayland Desktop Showcase.png",
        "Aurora-Wayland-Glass-Desktop.png(1).jpg",
        "Aurora-Wayland-Glass-Desktop.png",
        "Aurora Wayland Desktop - boot background.jpg",
    ),
}
RELATED_SESSION_ARTWORK = {
    "Duck-ai-image-2026-10-18-07-06(1).jpeg": RELATED_ARTWORK["aurora-and-mountain.jpg"],
    "Duck-ai-image-2026-10-18-06-36.jpeg": RELATED_ARTWORK["octavian-marine-dual-brand.jpg"],
}


def _select_artwork(source_dir: Path, required: dict, candidates: dict) -> dict:
    selected = {}
    for role, spec in required.items():
        if (source_dir / role).is_file():
            # Existing pinned names retain their exact dimensions/hash contract.
            # Corrupt pinned sources never silently fall back to other artwork.
            selected[role] = spec
            continue
        candidate = next((name for name in candidates.get(role, ()) if (source_dir / name).is_file()), None)
        if candidate is None:
            raise FileNotFoundError(
                f"no source artwork for {role}; looked for the pinned source and related local artwork"
            )
        selected[role] = {
            "id": spec["id"], "selector": spec["selector"],
            "background": spec["background"], "source_file": candidate,
            "related_artwork_fallback": True,
        }
    return selected


def generate(source_dir: Path, css_path: Path, manifest_path: Path) -> dict:
    specs = _select_artwork(source_dir, EXPECTED, RELATED_ARTWORK)
    return _generate(source_dir, css_path, manifest_path, specs, "CHM-EMBEDDED-WALLPAPERS-2")


def generate_session_branding(source_dir: Path, css_path: Path, manifest_path: Path) -> dict:
    specs = _select_artwork(source_dir, SESSION_BRANDING, RELATED_SESSION_ARTWORK)
    return _generate(source_dir, css_path, manifest_path, specs, "CHM-SESSION-BRANDING-2")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=Path("desktop/aurora/assets/library"))
    parser.add_argument("--css", type=Path, default=Path("desktop/aurora/assets/embedded-wallpapers.css"))
    parser.add_argument("--manifest", type=Path, default=Path("desktop/aurora/assets/embedded-wallpapers.json"))
    parser.add_argument("--session-branding", action="store_true",
                        help="embed pinned dual-brand JPEGs when present, otherwise use related checked-in artwork offline")
    args = parser.parse_args()
    if args.session_branding:
        result = generate_session_branding(args.source_dir, args.css, args.manifest)
    else:
        result = generate(args.source_dir, args.css, args.manifest)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
