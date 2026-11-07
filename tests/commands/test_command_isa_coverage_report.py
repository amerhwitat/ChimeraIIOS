#!/usr/bin/env python3
"""Exercise catalogue/provider counts without fabricating command executables."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/commands/build-command-isa-coverage.py"
with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp)
    repo = base / "repo"
    rootfs = base / "rootfs"
    (repo / "system/commands").mkdir(parents=True)
    (repo / "config").mkdir()
    (repo / "data/isa").mkdir(parents=True)
    (rootfs / "usr/bin").mkdir(parents=True)
    catalogue = {
        "linux_bash": ["echo", "printf", "missing-tool"],
        "macos_core": ["ls"],
        "windows_cmd_core": ["dir"],
        "powershell_core": ["Get-Process"],
        "vbscript_core": ["MsgBox"],
        "sql_server_core": ["SELECT"],
        "native_chimera": ["chimera-verified-test"],
    }
    (repo / "system/commands/chimera-command-list.json").write_text(json.dumps(catalogue), encoding="utf-8")
    (repo / "config/linux-command-registry.json").write_text(json.dumps({"groups": {}}), encoding="utf-8")
    (repo / "ISA.csv").write_text("architecture,mnemonic\nx86_64,NOP\n", encoding="utf-8")
    (repo / "data/isa/online-isa-index.json").write_text(json.dumps({"candidate_definition_count": 1}), encoding="utf-8")
    busybox = rootfs / "usr/bin/busybox"
    busybox.write_text("#!/bin/sh\nif [ \"$1\" = \"--list\" ]; then printf 'echo\\n'; fi\n", encoding="utf-8")
    busybox.chmod(0o755)
    (rootfs / "usr/bin/echo").symlink_to(busybox)
    (rootfs / "usr/bin/chimera-verified-test").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (rootfs / "usr/bin/chimera-verified-test").chmod(0o755)
    matrix = base / "linux-abi.json"
    matrix.write_text(json.dumps({"targets": []}), encoding="utf-8")
    report = base / "coverage.json"
    subprocess.run([
        sys.executable, str(SCRIPT), "--root", str(repo), "--busybox", str(busybox),
        "--rootfs", str(rootfs), "--native-matrix", str(matrix), "--output", str(report)
    ], check=True)
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["source_catalogue_unique_command_count"] == 9
    assert data["source_catalogue_candidate_inventory_allowlist_count"] == 2
    assert data["source_catalogue_candidate_only_count"] == 7
    assert data["source_catalogue_verified_hosted_provider_count"] == 3
    assert data["source_catalogue_unverified_provider_count"] == 6
    assert data["source_catalogue_provider_status_counts"]["busybox-applet"] == 1
    assert data["source_catalogue_provider_status_counts"]["shell-builtin"] == 1
    assert data["source_catalogue_provider_status_counts"]["hosted-linux-rootfs-executable"] == 1
    assert data["source_catalogue_provider_status_counts"]["compatibility-provider-required"] == 5
    assert data["source_catalogue_provider_status_counts"]["catalogued-provider-required"] == 1
    assert data["native_chimera_command_count"] == 1
    assert data["native_chimera_provider_count"] == 1
    assert data["native_chimera_source_implementation_count"] == 0
    assert data["native_chimera_koronos_runtime_verified_count"] == 0
    print("PASS unique catalogue count and verified-provider coverage are reported without fake binaries")
