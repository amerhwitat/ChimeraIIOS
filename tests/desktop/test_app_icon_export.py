#!/usr/bin/env python3
import json, pathlib, subprocess, tempfile
root=pathlib.Path(__file__).resolve().parents[2]
manifest=json.loads((root/"desktop/app-icons/manifest.json").read_text())
assert manifest["count"]==133, manifest.get("count")
assert len(manifest["apps"])==133
with tempfile.TemporaryDirectory() as tmp:
    subprocess.run(["python3",str(root/"tools/aurora/export-app-icon-theme.py"),
        "--sprite",str(root/"desktop/app-icons/catalog.svg"),
        "--manifest",str(root/"desktop/app-icons/manifest.json"),
        "--output",tmp],check=True)
    out=pathlib.Path(tmp)
    exported=json.loads((out/"manifest.json").read_text())
    assert exported["count"]==133
    for row in exported["icons"]:
        p=out/row["file"]
        assert p.is_file() and p.stat().st_size>100
        data=p.read_text()
        assert "<svg" in data and "</svg>" in data
print("PASS: all 133 Aurora app icons export as standalone SVG theme assets")
