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
recipes={"bash":"bash","zsh":"zsh","fish":"fish","dash":"dash","mksh":"mksh",
         "yash":"yash","nu":"nushell","elvish":"elvish","alacritty":"alacritty",
         "foot":"foot","blackbox":"blackbox","wezterm":"wezterm",
         "ghostty":"ghostty","contour":"contour"}
for binary, recipe in recipes.items():
    assert f"{binary}) build_{recipe}" in source_builder, f"missing source build dispatch for {binary}"
    assert f"build_{recipe}()" in source_builder, f"missing source build implementation for {binary}"
assert "git clone --depth 1" in source_builder
assert "verify_target_elf" in source_builder and "rev-parse HEAD" in source_builder
terminal_manifest=json.loads((root/"aurora/terminals/binary-manifest.json").read_text())["terminals"]
assert terminal_manifest["ghostty"]["release_tag"] == "v1.3.1"
assert terminal_manifest["ghostty"]["upstream_commit"] == "332b2aefc6e72d363aa93ab6ecfc86eeeeb5ed28"
assert terminal_manifest["contour"]["release_tag"] == "v0.6.3.8249"
assert terminal_manifest["contour"]["release_sha256"] == "526e5bdd241ecfd0b63cf3ec3cacf5cbf2609cb03070f46b06e19d4e6329f397"
assert "sha256sum --check" in source_builder and "v0.6.3.8249" in source_builder
assert 'install -D -m 0755 "$ROOTFS/usr/bin/contour" "$ROOTFS/usr/local/bin/contour"' in source_builder
for alias in ("chimera-terminal","chimera-terminals","chimera-shell-ar"):
    assert alias in (root/"tools/aurora/install-terminal-shell-suite.sh").read_text()
assert "rev-parse HEAD" in source_builder
print("PASS: 20 terminal and 8 shell providers are package-checked; launchers require installed executables")
