#!/usr/bin/env python3
"""Validate database build profiles without claiming runtime support."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
matrix = json.loads((root / "database/build-matrix.json").read_text(encoding="utf-8"))
registry = json.loads((root / "data/registry/databases.json").read_text(encoding="utf-8"))
engines = matrix.get("engines", [])
ids = [e.get("id") for e in engines]
if len(ids) != len(set(ids)):
    raise SystemExit("duplicate database engine id")
registry_ids = {e["id"] for e in registry.get("engines", [])}
missing = set(ids) - registry_ids
if missing:
    raise SystemExit("build matrix engines missing from data registry: " + ", ".join(sorted(missing)))
for engine in engines:
    for key in ("license", "upstream", "source", "integration", "build_profile", "ci", "status"):
        if not engine.get(key):
            raise SystemExit(f"{engine.get('id')}: missing {key}")
    if engine["build_profile"] == "official-container" and not engine.get("container"):
        raise SystemExit(f"{engine['id']}: official-container profile has no image")
    if engine["build_profile"] != "official-container" and engine.get("container"):
        raise SystemExit(f"{engine['id']}: unexpected container image")
for item in matrix.get("excluded_or_separately_classified", []):
    if not item.get("license") or not item.get("reason"):
        raise SystemExit(f"{item.get('id')}: missing license classification")
print(f"validated {len(engines)} database build profiles; {sum(bool(e.get('container')) for e in engines)} upstream images are pinned")
