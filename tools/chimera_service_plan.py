#!/usr/bin/env python3
"""Resolve and validate Chimera service selections from the shared registry."""
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path): return json.loads(Path(path).read_text())

def resolve(profile_id, requested, registry, profiles):
    profiles_by_id = {p["id"]: p for p in profiles["profiles"]}
    if profile_id not in profiles_by_id:
        raise ValueError(f"unknown profile: {profile_id}")
    selected = set(profiles_by_id[profile_id]["services"]) | set(requested)
    services = {s["id"]: s for s in registry["services"]}
    if not selected <= services.keys():
        raise ValueError("unknown requested service")
    changed = True
    while changed:
        changed = False
        for sid in list(selected):
            for dep in services[sid].get("dependencies", []):
                if dep not in selected:
                    selected.add(dep); changed = True
    graph = {sid: set(services[sid].get("dependencies", [])) & selected for sid in selected}
    order = []
    while graph:
        ready = sorted(sid for sid, deps in graph.items() if not deps)
        if not ready: raise ValueError("cyclic service dependency")
        order.extend(ready)
        for sid in ready: graph.pop(sid)
        for deps in graph.values(): deps.difference_update(ready)
    return order

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("profile"); ap.add_argument("services", nargs="*")
    args = ap.parse_args()
    registry = load(ROOT / "config/services/service-registry.json")
    profiles = load(ROOT / "config/services/service-profiles.json")
    print("\n".join(resolve(args.profile, args.services, registry, profiles)))

if __name__ == "__main__": main()
