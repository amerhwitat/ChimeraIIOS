#!/usr/bin/env python3
"""Tests for the native command catalogue, CHMCMD format and conformance runner."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools/commands"
SOURCE = ROOT / "src/chimera-command-compat/chimera-cmd.c"
EXPECTED_OFFICIAL = {"status": "not-run", "conformance_tested": 0, "not_implemented": 1613}
OFFICIAL_PROVIDERS = {
    "pwd", "echo", "ls", "cp", "mv", "touch", "mkdir", "rm", "cat", "clear",
    "whoami", "hostname", "date", "true", "false",
}
REAL_PROVIDERS = OFFICIAL_PROVIDERS | {
    "basename", "dirname", "head", "tail", "wc", "seq", "sleep", "uname",
    "readlink", "rmdir", "ln", "printenv", "env",
}


def run(script: str, *args: str, expect: int = 0) -> dict:
    proc = subprocess.run(
        [sys.executable, str(TOOLS / script), *args],
        cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if proc.returncode != expect:
        raise AssertionError(
            f"{script} returned {proc.returncode} (expected {expect})\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )
    return json.loads(proc.stdout) if proc.stdout.strip().startswith("{") else {}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="chimera-native-catalog-test-") as tmp:
        work = Path(tmp)
        catalogue = work / "native-command-catalog.json"
        binary = work / "native-commands.chmcmd"
        evidence = work / "evidence.json"

        # Forge metadata that claims a native implementation. The generator must
        # not promote this row: only real source-backed providers count.
        coverage = json.loads(
            (ROOT / "system/commands/command-isa-coverage.json").read_text(encoding="utf-8")
        )
        coverage["commands"].append({
            "name": "forged_metadata_only_command",
            "platforms": ["linux_bash"],
            "implementation": "native-source-implemented",
            "binary_status": "not-verified-in-repository",
        })
        forged_coverage = work / "coverage.json"
        forged_coverage.write_text(json.dumps(coverage), encoding="utf-8")

        generator_summary = run(
            "generate_native_command_catalog.py",
            "--isa-coverage", str(forged_coverage),
            "--output", str(catalogue),
        )

        doc = json.loads(catalogue.read_text(encoding="utf-8"))
        rows = doc["records"]
        assert doc["record_count"] == len(rows)
        assert doc["input_counts"]["command_isa_coverage_unique"] == 854
        assert doc["input_counts"]["command_runtime_capabilities_records"] == 4144
        assert doc["input_counts"]["native_command_candidates_records"] == 4084
        assert doc["provider_count"] == 28
        assert doc["implemented_count"] == 28
        assert doc["not_implemented_count"] == len(rows) - 28
        assert not doc["full_conformance"] and not doc["conformance_claim"]
        assert all(doc["official_status_snapshot"][key] == value
                   for key, value in EXPECTED_OFFICIAL.items())

        by_name = {row["name"]: row for row in rows}
        assert len(by_name) == len(rows), "duplicate catalogue rows"
        implemented = {name for name, row in by_name.items()
                       if row["implementation"] != "not_implemented"}
        assert implemented == REAL_PROVIDERS, implemented
        assert by_name["forged_metadata_only_command"]["implementation"] == "not_implemented"

        source = SOURCE.read_text(encoding="utf-8")
        install = (ROOT / "tools/build-chimera-command-compat.sh").read_text(encoding="utf-8")
        for name in implemented:
            row = by_name[name]
            function = row["implementation_details"]["function"]
            assert f'strcmp(cmd, "{name}")' in source, f"no dispatch for {name}"
            assert f"static int {function}(" in source, f"no function for {name}"
            assert re.search(rf"^\s*{name}$", install, re.M), f"no alias for {name}"
            assert row["operands"] or name in {"pwd", "true", "false", "clear",
                                               "whoami", "hostname", "date", "uname"}
            assert row["implementation_reason"] is None
            assert row["effects_on_registers"] == []

        for name, row in by_name.items():
            if name not in implemented:
                assert row["implementation"] == "not_implemented"
                assert row["implementation_reason"], f"missing reason for {name}"
                assert row["operands"] == [] and row["options"] == []
                assert row["permission_flags"] == 0

        build_summary = run(
            "build_native_command_format.py",
            "--catalogue", str(catalogue),
            "--output", str(binary),
        )
        assert build_summary["record_count"] == len(rows)
        assert build_summary["implemented"] == 28

        validate_summary = run(
            "validate_native_command_format.py",
            "--binary", str(binary),
            "--catalogue", str(catalogue),
        )
        assert validate_summary["valid"] is True
        assert validate_summary["record_count"] == len(rows)
        assert validate_summary["implemented"] == 28

        corrupted = work / "corrupted.chmcmd"
        data = bytearray(binary.read_bytes())
        data[8] ^= 0xFF  # first record magic byte
        corrupted.write_bytes(data)
        run("validate_native_command_format.py", "--binary", str(corrupted),
            "--catalogue", str(catalogue), expect=1)

        conformance = run(
            "run_command_conformance.py",
            "--source", str(SOURCE),
            "--output", str(evidence),
        )
        ev = json.loads(evidence.read_text(encoding="utf-8"))
        assert ev["official_status_unchanged"] is True
        assert ev["conformance_claim"] is False and ev["full_catalog_run"] is False
        assert all(ev["official_status"][key] == value
                   for key, value in EXPECTED_OFFICIAL.items())
        assert ev["isa_results"]["x86_64"]["executed"] > 0
        assert ev["isa_results"]["x86_64"]["failed"] == 0
        for isa in ("aarch64", "riscv64"):
            assert ev["isa_results"][isa]["executed"] == 0
            assert ev["isa_results"][isa]["status"] == "not-run"
        assert conformance["failed"] == 0

    print("native command catalogue tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
