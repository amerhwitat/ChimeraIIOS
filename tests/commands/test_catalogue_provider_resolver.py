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
    ss64 = temp / "ss64.json"
    catalog.write_text(json.dumps({"linux_bash": ["printf", "case", "chimera-no-such-command-9f3"]}), encoding="utf-8")
    ss64.write_text(json.dumps({"platforms":{"linux_bash":{"commands":[
        {"name":"chimera-ss64-only-command-7d2","source":"https://ss64.com/bash/chimera-ss64-only-command-7d2.html"},
        {"name":"Arguments","source":"https://ss64.com/bash/syntax-args.html"},
        {"name":".bashrc","source":"https://ss64.com/bash/syntax-bashrc.html"}
    ]}}}), encoding="utf-8")
    subprocess.run([sys.executable, str(SCRIPT), "--catalog", str(catalog),
                    "--ss64", str(ss64), "--output", str(report), "--no-install"], check=True)
    data = json.loads(report.read_text(encoding="utf-8"))
    rows = {row["name"]: row for row in data["commands"]}
    assert rows["case"]["status"] == "provided-by-shell-builtin"
    assert rows["printf"]["status"] == "existing-executable-provider"
    missing = rows["chimera-no-such-command-9f3"]
    assert missing["status"] == "provider-not-found-yet"
    ss64_missing = rows["chimera-ss64-only-command-7d2"]
    assert ss64_missing["status"] == "provider-not-found-yet"
    assert "Arguments" not in rows and ".bashrc" not in rows
    assert "path" not in missing and "binary" not in missing
    strict = subprocess.run([sys.executable, str(SCRIPT), "--catalog", str(catalog),
                             "--ss64", str(ss64), "--output", str(report),
                             "--no-install", "--require-all"], text=True, capture_output=True)
    assert strict.returncode == 1, (strict.returncode, strict.stdout, strict.stderr)
    assert "unresolved Linux command providers" in strict.stderr
    print("PASS catalogue resolver records real providers, rejects unresolved entries in strict mode, and never fabricates executables")
