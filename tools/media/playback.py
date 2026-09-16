#!/usr/bin/env python3
"""Provider-neutral playback helper. Uses GStreamer when available without shell evaluation."""
from __future__ import annotations
import shutil, subprocess
from pathlib import Path

def play(path: Path) -> int:
    gst = shutil.which("gst-play-1.0")
    if gst:
        return subprocess.run([gst, str(path)], check=False).returncode
    raise RuntimeError("GStreamer gst-play-1.0 is not installed")

if __name__ == "__main__":
    import argparse
    p=argparse.ArgumentParser(); p.add_argument("path", type=Path); args=p.parse_args(); raise SystemExit(play(args.path))
