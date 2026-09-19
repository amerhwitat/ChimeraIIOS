#!/usr/bin/env python3
"""Aurora wallpaper scheduler reference implementation.

This module manages policy and rotation state; compositor-specific presentation
belongs to the desktop adapter layer.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import json
import random
from typing import Iterable

SUPPORTED = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".tif", ".tiff", ".bmp"}


@dataclass(frozen=True)
class Wallpaper:
    path: Path
    digest: str


def discover(root: Path) -> list[Wallpaper]:
    items: list[Wallpaper] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            items.append(Wallpaper(path, digest))
    return items


def choose(items: Iterable[Wallpaper], previous_digest: str | None = None) -> Wallpaper | None:
    pool = [item for item in items if item.digest != previous_digest]
    if not pool:
        pool = list(items)
    return random.choice(pool) if pool else None


def next_change(interval_seconds: int = 3600, now: datetime | None = None) -> datetime:
    now = now or datetime.now().astimezone()
    return now + timedelta(seconds=max(1, interval_seconds))


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"current": None, "changed_at": None}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, wallpaper: Wallpaper, changed_at: datetime | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "current": str(wallpaper.path),
        "sha256": wallpaper.digest,
        "changed_at": (changed_at or datetime.now().astimezone()).isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Aurora wallpaper scheduler reference tool")
    parser.add_argument("library", type=Path)
    parser.add_argument("--state", type=Path, default=Path.home() / ".chimera" / "wallpaper-state.json")
    args = parser.parse_args()

    wallpapers = discover(args.library)
    state = load_state(args.state)
    selected = choose(wallpapers, state.get("sha256"))
    if selected:
        save_state(args.state, selected)
        print(selected.path)
    else:
        print("No supported wallpapers found.")
