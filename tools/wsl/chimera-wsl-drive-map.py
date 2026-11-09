#!/usr/bin/env python3
"""Expose WSL2's existing /mnt/<drive-letter> mounts under /mnt/drive/<letter>.

This is a host-side WSL namespace convenience only. It does not implement a
Koronos NTFS/DrvFs kernel driver and never mounts or formats a volume.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import string
import sys


def map_drives(mnt: Path) -> list[str]:
    drive_root = mnt / "drive"
    drive_root.mkdir(mode=0o755, parents=True, exist_ok=True)
    mapped: list[str] = []
    for letter in string.ascii_lowercase:
        source = mnt / letter
        if not source.is_dir():
            continue
        for alias in (letter, letter.upper()):
            target = drive_root / alias
            if target.is_symlink():
                if target.resolve(strict=False) == source.resolve(strict=False):
                    continue
                raise RuntimeError(f"refusing to replace unrelated symlink: {target}")
            if target.exists():
                # Never merge/copy into an existing directory; preserve user data.
                raise RuntimeError(f"refusing to replace existing path: {target}")
            target.symlink_to(source, target_is_directory=True)
        mapped.append(letter)
    return mapped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mnt-root", type=Path, default=Path("/mnt"),
                        help="WSL mount root (default: /mnt; test override supported)")
    args = parser.parse_args()
    try:
        mapped = map_drives(args.mnt_root)
    except (OSError, RuntimeError) as exc:
        print(f"chimera-wsl-drive-map: {exc}", file=sys.stderr)
        return 1
    print("Mapped Windows drives under /mnt/drive: " +
          (", ".join(mapped) if mapped else "(no mounted drive letters found)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
