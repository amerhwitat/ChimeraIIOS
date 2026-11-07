#!/usr/bin/env python3
"""Strict native-command coverage gate accepts real providers and rejects missing commands."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/commands/verify-command-provider-coverage.py"

with tempfile.TemporaryDirectory() as temp:
    base = Path(temp)
    rootfs = base / "rootfs"
    bindir = rootfs / "usr/bin"
    bindir.mkdir(parents=True)
    (bindir / "bash").write_text("#!/bin/sh\\nexit 0\\n", encoding="utf-8")
    (bindir / "echo").write_text("#!/bin/sh\\nprintf '%s\\n' \"$@\"\\n", encoding="utf-8")
    for name in ("bash", "echo"):
        (bindir / name).chmod(0o755)
    caps = base / "capabilities.json"
    caps.write_text(json.dumps({"commands": [
        {"name": "echo", "mode": "native", "platforms": ["linux-bash"]},
        {"name": "chimera-missing-native-test", "mode": "native", "platforms": ["chimera-native"]},
        {"name": "printf", "mode": "shell-builtin", "platforms": ["linux-bash"]},
        {"name": "if", "mode": "language-feature", "platforms": ["linux-bash"]},
    ]}), encoding="utf-8")
    failed = subprocess.run([sys.executable, str(SCRIPT), str(rootfs), str(caps),
                             "x86_64", "--require-native"], text=True, capture_output=True)
    assert failed.returncode == 1, (failed.returncode, failed.stdout, failed.stderr)
    assert "chimera-missing-native-test=native-implementation-not-staged" in failed.stderr
    (bindir / "chimera-missing-native-test").write_text("#!/bin/sh\\nexit 0\\n", encoding="utf-8")
    (bindir / "chimera-missing-native-test").chmod(0o755)
    passed = subprocess.run([sys.executable, str(SCRIPT), str(rootfs), str(caps),
                             "x86_64", "--require-native"], text=True, capture_output=True)
    assert passed.returncode == 0, (passed.returncode, passed.stdout, passed.stderr)
    report = json.loads((rootfs / "usr/share/chimera/commands/command-provider-coverage.json").read_text())
    assert report["catalog_count"] == 4
    print("PASS strict native provider coverage rejects missing executables and accepts real staged files")
