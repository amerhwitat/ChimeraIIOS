#!/usr/bin/env python3
"""Record only actual executable shell and terminal providers in a target rootfs."""
from __future__ import annotations
import argparse, json, os, stat
from pathlib import Path

SEARCH = ("usr/local/bin", "usr/local/sbin", "usr/bin", "usr/sbin", "bin", "sbin")

def resolve_target(root: Path, name: str):
    for directory in SEARCH:
        candidate = root / directory / name
        current = candidate
        seen = set()
        try:
            for _ in range(32):
                key = str(current)
                if key in seen:
                    break
                seen.add(key)
                info = os.lstat(current)
                if stat.S_ISLNK(info.st_mode):
                    target = os.readlink(current)
                    current = (root / target.lstrip("/")) if os.path.isabs(target) else (current.parent / target)
                    current = Path(os.path.normpath(current))
                    if not current.is_relative_to(root):
                        break
                    continue
                if stat.S_ISREG(info.st_mode) and info.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
                    return "/" + current.relative_to(root).as_posix()
                break
        except (FileNotFoundError, NotADirectoryError, PermissionError, OSError):
            continue
    return None

def inspect(root: Path, registry_path: Path, kind: str):
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    rows = []
    source_rows = registry.get("entries", [])
    if kind == "shell":
        source_rows = registry.get("entries", [])
    for item in source_rows:
        binary = item.get("binary")
        path = resolve_target(root, binary) if binary else None
        rows.append({
            "id": item.get("id"),
            "name": item.get("name"),
            "kind": kind,
            "binary": binary,
            "path": path,
            "source": item.get("source"),
            "license": item.get("license"),
            "status": "present-executable-not-runtime-tested" if path else "not-installed-or-no-provider",
        })
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rootfs", type=Path, required=True)
    ap.add_argument("--shell-registry", type=Path, required=True)
    ap.add_argument("--terminal-registry", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    root = args.rootfs.resolve()
    shells = inspect(root, args.shell_registry, "shell")
    terminals = inspect(root, args.terminal_registry, "terminal")
    result = {
        "schema": "CHIMERA-TERMINAL-SHELL-PROVIDERS-1",
        "rootfs": "/",
        "policy": "A provider is present only when a real executable file exists in the target rootfs. Presence does not claim launch/runtime acceptance. Missing providers remain explicit.",
        "shells": shells,
        "terminals": terminals,
        "summary": {
            "shells_registered": len(shells),
            "shells_present": sum(x["path"] is not None for x in shells),
            "terminals_registered": len(terminals),
            "terminals_present": sum(x["path"] is not None for x in terminals),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
