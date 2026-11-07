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
coverage_aliases = {str(name).casefold() for name in coverage.get(
    "linux_abi_multicall_aliases", coverage.get("native_source_commands", []))}
rows = {str(row.get("command", row.get("name", ""))).casefold(): row for row in coverage["commands"]}

catalogue_count = coverage.get("source_catalogue_unique_command_count",
                               coverage.get("counts", {}).get("unique_commands"))
assert len(catalogue) == catalogue_count, (len(catalogue), catalogue_count)
assert aliases == coverage_aliases, (sorted(aliases - coverage_aliases), sorted(coverage_aliases - aliases))
assert aliases <= catalogue, sorted(aliases - catalogue)
alias_count = coverage.get("linux_abi_multicall_alias_count",
                           coverage.get("counts", {}).get("native_source_commands"))
assert alias_count == len(aliases), (alias_count, len(aliases))
assert catalogue <= set(rows), (len(rows), len(catalogue), sorted(catalogue - set(rows)))
for alias in aliases:
    assert rows[alias]["implementation"] == "native-source-implemented", alias
print(f"PASS: {len(catalogue)} catalogue commands, {len(aliases)} native source aliases, coverage rows aligned.")
