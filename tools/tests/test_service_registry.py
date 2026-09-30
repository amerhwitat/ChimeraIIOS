#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVICES = json.loads((ROOT / "config/services/service-registry.json").read_text())
PROFILES = json.loads((ROOT / "config/services/service-profiles.json").read_text())
GRAPH = json.loads((ROOT / "config/services/dependency-graph.json").read_text())

assert SERVICES["schema"] == "chimera-service-registry-v1"
assert PROFILES["schema"] == "chimera-service-profile-v1"
assert GRAPH["schema"] == "chimera-service-graph-v1"

services = SERVICES["services"]
ids = [s["id"] for s in services]
assert len(ids) == len(set(ids)), "duplicate service ID"
known = set(ids)
for service in services:
    for dep in service.get("dependencies", []):
        assert dep in known, f"dangling dependency: {service['id']} -> {dep}"

profiles = {p["id"]: p for p in PROFILES["profiles"]}
required = {"minimal-desktop", "developer-workstation", "enterprise-server", "full-chimera-enterprise"}
assert required <= profiles.keys()
for profile in profiles.values():
    for service_id in profile["services"]:
        assert service_id in known, f"profile references unknown service: {service_id}"

# Verify the published order contains every service exactly once.
order = GRAPH["order"]
assert set(order) == known
assert len(order) == len(known)
position = {sid: i for i, sid in enumerate(order)}
for service in services:
    for dep in service.get("dependencies", []):
        assert position[dep] < position[service["id"]], f"dependency order violation: {dep} -> {service['id']}"

print("PASS: service registry, profiles and dependency graph are valid")
