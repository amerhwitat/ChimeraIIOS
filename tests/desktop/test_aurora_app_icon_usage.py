#!/usr/bin/env python3
import json, pathlib
root=pathlib.Path(__file__).resolve().parents[2]
manifest=json.loads((root/"desktop/app-icons/manifest.json").read_text())
ids={row["id"] for row in manifest["apps"]}
assert len(ids)==133
shell=(root/"desktop/aurora-shell/assets/shell.js").read_text()
css=(root/"desktop/aurora-shell/assets/shell.css").read_text()
for item in ("APP_ICON_ALIASES","catalog.svg#app-","manifest.json","iconVisual","loadAppIconManifest"):
    assert item in shell, f"Aurora shell does not use generated app icons: {item}"
for item in (".app-icon-art",".glyph.has-art",".dock-icon",".tb-icon",".sm-icon"):
    assert item in css, f"missing Aurora app icon style: {item}"
for expected in ("file-manager","terminal","voiceconnect","network","settings","system-monitor","aurora-media-player","store","about","docs"):
    assert expected in ids, f"desktop default icon missing from sprite: {expected}"
build=(root/"live-image/build.sh").read_text()
assert 'desktop/app-icons/catalog.svg' in build and 'desktop/app-icons/manifest.json' in build
print(f"PASS: {len(ids)} generated Aurora app icons are wired into desktop, dock, taskbar and launcher.")
