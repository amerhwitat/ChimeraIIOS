#!/usr/bin/env python3
"""Dependency-free CI validation for the Chimera Cloud Fabric."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "tools" / "cloud" / "chimera_cloud.py"
REGISTRY = ROOT / "cloud" / "providers.json"

providers = json.loads(REGISTRY.read_text(encoding="utf-8"))["providers"]
required = {"kubernetes", "openshift", "openstack", "aws", "azure", "gcp"}
missing = required - providers.keys()
if missing:
    raise SystemExit(f"missing providers: {sorted(missing)}")

subprocess.run([sys.executable, str(CLI), "providers"], cwd=ROOT, check=True)
with tempfile.TemporaryDirectory() as d:
    plan = Path(d) / "plan.json"
    subprocess.run([sys.executable, str(CLI), "plan", "kubernetes", "--output", str(plan)], cwd=ROOT, check=True)
    data = json.loads(plan.read_text(encoding="utf-8"))
    assert data["execution"] == "explicit-apply"
print("Chimera Cloud Fabric validation passed")
