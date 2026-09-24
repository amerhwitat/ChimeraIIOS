#!/usr/bin/env python3
"""Resolve Aurora file/application associations from one shared registry."""

from __future__ import annotations
import argparse, json, mimetypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "desktop/file_associations/file_association_registry.json"

def resolve(path: Path) -> dict:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    ext = path.suffix.lower()
    mime, _ = mimetypes.guess_type(path.name, strict=False)
    mime = data.get("extensions", {}).get(ext, mime or "application/octet-stream")
    apps = list(data.get("mime_types", {}).get(mime, []))
    kind = "video" if mime.startswith("video/") else "media" if mime.startswith(("audio/","image/")) else "open"
    return {"path": str(path), "extension": ext, "mime_type": mime,
            "applications": apps, "default": apps[0] if apps else None,
            "actions": data.get("actions", {}).get(kind, [])}

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("path", type=Path)
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    print(json.dumps(resolve(a.path), ensure_ascii=False, indent=2 if a.json else None))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
