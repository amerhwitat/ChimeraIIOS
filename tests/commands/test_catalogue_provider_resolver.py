#!/usr/bin/env python3
"""Contract test: catalogue resolution records providers but never fabricates binaries."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/commands/resolve-catalogue-command-providers.py"
with tempfile.TemporaryDirectory() as temp:
    temp = Path(temp)
    catalog = temp / "catalog.json"
    report = temp / "report.json"
    catalog.write_text(json.dumps({"linux_bash": ["printf", "case", "chimera-no-such-command-9f3"]}), encoding="utf-8")
    subprocess.run([sys.executable, str(SCRIPT), "--catalog", str(catalog),
                    "--output", str(report), "--no-install"], check=True)
    data = json.loads(report.read_text(encoding="utf-8"))
    rows = {row["name"]: row for row in data["commands"]}
    assert rows["case"]["status"] == "provided-by-shell-builtin"
    assert rows["printf"]["status"] == "existing-executable-provider"
    missing = rows["chimera-no-such-command-9f3"]
    assert missing["status"] == "provider-not-found-yet"
    assert "path" not in missing and "binary" not in missing
    print("PASS catalogue resolver records real providers and never fabricates missing executables")
