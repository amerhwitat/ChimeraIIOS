#!/usr/bin/env python3
"""Generate non-destructive Chimera edition scaffolds."""
from __future__ import annotations
import argparse, json
from pathlib import Path

EDITIONS = {
    "desktop": ["kernel", "drivers", "apps", "data", "ai", "observability", "repair", "tests"],
    "server": ["kernel", "services", "network", "data", "ai", "observability", "security", "repair", "tests"],
    "mobile": ["microkernel", "drivers", "ui", "data", "ai", "power", "observability", "repair", "tests"],
    "edge": ["kernel", "drivers", "iot", "data", "ai", "network", "observability", "repair", "tests"],
    "cvel": ["virtual-cpu", "virtual-memory", "devices", "data", "ai", "network", "observability", "repair", "tests"],
}
COMMON = ["compiler", "data", "observability", "security", "repair", "research"]

def scaffold(root: Path, editions: list[str], force: bool = False) -> dict:
    created = []
    for edition in editions:
        if edition not in EDITIONS:
            raise ValueError(f"unknown edition: {edition}")
        for name in [*EDITIONS[edition], *COMMON]:
            path = root / edition / name
            if path.exists() and not force:
                continue
            path.mkdir(parents=True, exist_ok=True)
            marker = path / ".chimera-scaffold"
            if force or not marker.exists():
                marker.write_text("generated-by=chimera_scaffold\n", encoding="utf-8")
            created.append(str(path))
    manifest = {"schema": "CHIMERA-SCAFFOLD-MANIFEST-1", "editions": editions, "created": created}
    (root / "chimera_scaffold_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("scaffolds"))
    p.add_argument("--edition", action="append", choices=sorted(EDITIONS), default=[])
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    editions = args.edition or list(EDITIONS)
    print(json.dumps(scaffold(args.root, editions, args.force), indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
