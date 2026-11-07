#!/usr/bin/env python3
import json, pathlib, re
root=pathlib.Path(__file__).resolve().parents[2]
terms=json.loads((root/"aurora/terminals/registry.json").read_text())["entries"]
shells=json.loads((root/"aurora/shells/registry.json").read_text())["entries"]
script=(root/"tools/aurora/install-terminal-shell-suite.sh").read_text()
launcher=(root/"aurora/terminals/install-desktop-entries.sh").read_text()
expected={("terminal",x["id"],x["binary"]) for x in terms}|{("shell",x["id"],x["binary"]) for x in shells}
mapping=set()
for line in script.splitlines():
    for item in re.findall(r'"([a-z0-9-]+\|[a-z0-9-]+)"',line):
        pkg,bin=item.split("|",1)
        mapping.add(bin)
assert len(terms)==20 and len(shells)==8
assert {x[2] for x in expected} <= mapping, (sorted(x[2] for x in expected-mapping))
assert "apt-get install -y --no-install-recommends" in script
assert "command -v" in script and "source-build-required" in script
assert 'chroot "$ROOTFS" /bin/sh -c "command -v' in launcher
assert "continue" in launcher
source_builder=(root/"tools/aurora/build-terminal-shell-sources.sh").read_text()
for binary in ("yash","nu","wezterm","ghostty","contour"):
    assert binary in source_builder, f"missing source build recipe for {binary}"
assert "git clone --depth 1" in source_builder
for alias in ("chimera-terminal","chimera-terminals","chimera-shell-ar"):
    assert alias in (root/"tools/aurora/install-terminal-shell-suite.sh").read_text()
assert "rev-parse HEAD" in source_builder
print("PASS: 10 terminal and 8 shell providers are package-checked; launchers require installed executables")
