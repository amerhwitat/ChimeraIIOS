#!/usr/bin/env python3
"""Tests for the native command catalogue, CHMCMD format and conformance runner.

Fails if any row has empty operand/option/register-effect descriptors, if a
metadata-only row is promoted to implemented, or if a malformed/empty record is
accepted by the builder or validator.
"""
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
OPERAND_FIELDS = {"kind", "name", "required", "type", "value_constraints",
                  "source_field", "evidence"}
OPTION_FIELDS = {"kind", "name", "flag", "form", "value_type", "default",
                 "source_field", "evidence"}
EFFECTS_FIELDS = {"visibility", "reads", "writes", "clobbers", "status",
                  "reason", "source_field", "evidence"}
STATUS_FIELDS = {"status", "visibility", "source_field", "evidence", "reason"}


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

        # Forge metadata that claims a native implementation. The generator
        # must not promote this row: only real source-backed providers count.
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

        counts = doc["descriptor_counts"]
        assert counts["rows_with_operands"] == len(rows), counts
        assert counts["rows_with_options"] == len(rows), counts
        assert counts["rows_with_effects_on_registers"] == len(rows), counts
        assert counts["rows_with_register_effects_status_object"] == len(rows), counts

        by_name = {row["name"]: row for row in rows}
        assert len(by_name) == len(rows), "duplicate catalogue rows"
        implemented = {name for name, row in by_name.items()
                       if row["implementation"] != "not_implemented"}
        assert implemented == REAL_PROVIDERS, implemented
        assert by_name["forged_metadata_only_command"]["implementation"] == "not_implemented"

        source = SOURCE.read_text(encoding="utf-8")
        install = (ROOT / "tools/build-chimera-command-compat.sh").read_text(encoding="utf-8")
        for name, row in by_name.items():
            # Every row, implemented or not, carries structured descriptors.
            assert isinstance(row["operands"], list) and row["operands"]
            assert isinstance(row["options"], list) and row["options"]
            for operand in row["operands"]:
                assert isinstance(operand, dict) and operand
                assert OPERAND_FIELDS.issubset(operand), (name, operand)
            for option in row["options"]:
                assert isinstance(option, dict) and option
                assert OPTION_FIELDS.issubset(option), (name, option)
            effects = row["effects_on_registers"]
            assert isinstance(effects, dict) and effects
            assert EFFECTS_FIELDS.issubset(effects), (name, effects)
            assert effects["visibility"] == "not-isa-visible"
            assert effects["status"] == "no-architectural-register-effects"
            status = row["register_effects_status"]
            assert isinstance(status, dict) and status
            assert STATUS_FIELDS.issubset(status), (name, status)

            if name in implemented:
                function = row["implementation_details"]["function"]
                assert f'strcmp(cmd, "{name}")' in source, f"no dispatch for {name}"
                assert f"static int {function}(" in source, f"no function for {name}"
                assert re.search(rf"^\s*{name}$", install, re.M), f"no alias for {name}"
                assert row["implementation_reason"] is None
            else:
                assert row["implementation"] == "not_implemented"
                assert row["implementation_reason"], f"missing reason for {name}"
                assert row["isa_targets"] == []
                assert row["permission_flags"] == 0
                assert all(item["evidence"] == "no operand metadata in source catalog"
                           for item in row["operands"])
                assert all(item["evidence"] == "no option metadata in source catalog"
                           for item in row["options"])

        build_summary = run(
            "build_native_command_format.py",
            "--catalogue", str(catalogue),
            "--output", str(binary),
        )
        assert build_summary["record_count"] == len(rows)
        assert build_summary["implemented"] == 28
        assert all(value == len(rows)
                   for value in build_summary["descriptor_counts"].values())

        validate_summary = run(
            "validate_native_command_format.py",
            "--binary", str(binary),
            "--catalogue", str(catalogue),
        )
        assert validate_summary["valid"] is True
        assert validate_summary["record_count"] == len(rows)
        assert validate_summary["implemented"] == 28
        assert all(validate_summary[key] == len(rows) for key in (
            "rows_with_operands", "rows_with_options",
            "rows_with_effects_on_registers",
            "rows_with_register_effects_status_object",
        ))

        # A row with an empty descriptor array must be rejected by both the
        # builder and the validator.
        bad = json.loads(catalogue.read_text(encoding="utf-8"))
        bad["records"][0]["operands"] = []
        bad_catalogue = work / "bad-catalogue.json"
        bad_catalogue.write_text(json.dumps(bad), encoding="utf-8")
        run("build_native_command_format.py", "--catalogue", str(bad_catalogue),
            "--output", str(work / "bad.chmcmd"), expect=1)
        run("validate_native_command_format.py", "--binary", str(binary),
            "--catalogue", str(bad_catalogue), expect=1)

        bad_status = json.loads(catalogue.read_text(encoding="utf-8"))
        bad_status["records"][1]["register_effects_status"] = "not-isa-visible"
        bad_status_path = work / "bad-status.json"
        bad_status_path.write_text(json.dumps(bad_status), encoding="utf-8")
        run("validate_native_command_format.py", "--binary", str(binary),
            "--catalogue", str(bad_status_path), expect=1)

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
