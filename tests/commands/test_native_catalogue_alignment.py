#!/usr/bin/env python3
"""Ensure the command catalogue, native policy and coverage inventory cannot drift."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
catalog = json.loads((ROOT / "system/commands/chimera-command-list.json").read_text(encoding="utf-8"))
policy = json.loads((ROOT / "system/commands/compatibility-binary-policy.json").read_text(encoding="utf-8"))
coverage = json.loads((ROOT / "system/commands/command-isa-coverage.json").read_text(encoding="utf-8"))

fields = ("linux_bash", "macos_core", "windows_cmd_core", "powershell_core",
          "vbscript_core", "sql_server_core", "native_chimera")
catalogue = {
    str(item.get("name") if isinstance(item, dict) else item).strip().casefold()
    for field in fields for item in catalog.get(field, [])
}
aliases = {str(name).casefold() for name in policy["native_build"]["multicall_aliases"]}
coverage_aliases = {str(name).casefold() for name in coverage["native_source_commands"]}
rows = {str(row["name"]).casefold(): row for row in coverage["commands"]}

assert len(catalogue) == coverage["counts"]["unique_commands"], (
    len(catalogue), coverage["counts"]["unique_commands"])
assert aliases == coverage_aliases, (sorted(aliases - coverage_aliases), sorted(coverage_aliases - aliases))
assert aliases <= catalogue, sorted(aliases - catalogue)
assert coverage["counts"]["native_source_commands"] == len(aliases)
assert len(rows) == len(catalogue)
for alias in aliases:
    assert rows[alias]["implementation"] == "native-source-implemented", alias
print(f"PASS: {len(catalogue)} catalogue commands, {len(aliases)} native source aliases, coverage rows aligned.")
