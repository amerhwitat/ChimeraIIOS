#!/usr/bin/env python3
"""Safe Chimera build/test diagnosis and allowlisted repair runner."""
from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path

ACTIONS = {
    "configure": ["cmake", "-S", ".", "-B", "build"],
    "build": ["cmake", "--build", "build", "--parallel"],
    "test": ["ctest", "--test-dir", "build", "--output-on-failure"],
}

def diagnose(root: Path) -> dict:
    build = root / "build"
    cache = build / "CMakeCache.txt"
    return {
        "schema": "CHIMERA-REPAIR-REPORT-1",
        "root": str(root),
        "build_dir_exists": build.is_dir(),
        "cmake_cache_exists": cache.is_file(),
        "recommended_actions": (["configure"] if not cache.is_file() else []) + ["build", "test"],
    }

def apply(root: Path, action: str) -> int:
    if action not in ACTIONS:
        raise ValueError(f"action is not allowlisted: {action}")
    return subprocess.run(ACTIONS[action], cwd=root, check=False).returncode

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--action", choices=sorted(ACTIONS), action="append")
    p.add_argument("--apply", action="store_true", help="execute only allowlisted local actions")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    report = diagnose(args.root.resolve())
    if args.json or not args.apply:
        print(json.dumps(report, indent=2, sort_keys=True))
    if not args.apply:
        return 0
    for action in args.action or report["recommended_actions"]:
        rc = apply(args.root.resolve(), action)
        if rc:
            return rc
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
