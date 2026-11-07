#!/usr/bin/env python3
"""Validate native provider declarations and the complete multicall rootfs contract."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / "system/commands/native-provider-aliases.json").read_text(encoding="utf-8"))
commands = json.loads((ROOT / "system/commands/chimera-command-list.json").read_text(encoding="utf-8"))
catalog = set(commands["native_chimera"])
aliases = data["aliases"]
assert aliases and set(aliases).issubset(catalog)
for name, entry in aliases.items():
    provider = entry["provider"]
    assert provider.startswith("/") and ".." not in Path(provider).parts
    assert entry.get("description")

generator = (ROOT / "tools/commands/generate_runtime_manifest.py").read_text(encoding="utf-8")
stager = (ROOT / "tools/commands/stage-native-script-providers.py").read_text(encoding="utf-8")
assert "native-provider-aliases.json" in generator
assert "native-provider-aliases.json" in stager and "verified-provider-symlink" in stager
explicit = set(re.findall(r'^\s*"([^"]+)": "/usr/(?:bin|sbin|local/bin)/[^"]+",?$', generator, re.M))
mapped = explicit | set(aliases)
missing = set(catalog) - mapped
assert not missing, f"Chimera-native catalogue commands without a real provider declaration: {sorted(missing)}"

# The compiled multicall, rootfs symlink set, runtime manifest and coverage
# inventory must all agree on the same 25 source-backed Linux command aliases.
policy = json.loads((ROOT / "system/commands/compatibility-binary-policy.json").read_text(encoding="utf-8"))
coverage = json.loads((ROOT / "system/commands/command-isa-coverage.json").read_text(encoding="utf-8"))
multicall = set(policy["native_build"]["multicall_aliases"])
assert len(multicall) == 25
assert multicall <= set(commands["linux_bash"])

build_script = (ROOT / "tools/build-chimera-command-compat.sh").read_text(encoding="utf-8")
block = re.search(r"NATIVE_COMMANDS=\(\s*(.*?)\s*\)", build_script, re.S)
assert block, "rootfs native command symlink list missing"
staged = set(re.findall(r"^\s*([a-z][a-z0-9_-]*)\s*$", block.group(1), re.M))
assert staged == multicall, (sorted(multicall - staged), sorted(staged - multicall))

source = (ROOT / "src/chimera-command-compat/chimera-cmd.c").read_text(encoding="utf-8")
dispatch = set(re.findall(r'!strcmp\(cmd,\s*"([^"]+)"\)', source))
assert multicall <= dispatch, sorted(multicall - dispatch)

marker = 'cat > "$CMDROOT/registry.tsv" <<\'REGISTRY\'\n'
registry_block = build_script.split(marker, 1)[1].split("\nREGISTRY", 1)[0]
registry_native = set()
for line in registry_block.splitlines():
    fields = line.split("\t")
    if len(fields) >= 4 and fields[2:4] == ["native", "chimera-cmd"]:
        registry_native.add(fields[0])
assert multicall <= registry_native, sorted(multicall - registry_native)

coverage_rows = {row["name"].casefold(): row for row in coverage["commands"]}
assert multicall == {name.casefold() for name in coverage["native_source_commands"]}
assert all(coverage_rows[name]["implementation"] == "native-source-implemented" for name in multicall)

shell_ar = (ROOT / "tools/commands/chimera-shell-ar").read_text(encoding="utf-8")
assert "CHIMERA_LANG=ar" in shell_ar and "exec /usr/bin/chimera-shell" in shell_ar
print(f"PASS {len(catalog)} Chimera-native catalogue names have provider declarations; all {len(multicall)} multicall aliases are built and registered.")
