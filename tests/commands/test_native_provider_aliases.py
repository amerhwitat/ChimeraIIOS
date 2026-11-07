#!/usr/bin/env python3
"""Validate that native provider aliases point to real executable providers."""
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

shell_ar = (ROOT / "tools/commands/chimera-shell-ar").read_text(encoding="utf-8")
assert "CHIMERA_LANG=ar" in shell_ar and "exec /usr/bin/chimera-shell" in shell_ar
print(f"PASS {len(catalog)} Chimera-native command names have explicit provider declarations; missing provider files remain build failures")
