#!/usr/bin/env python3
"""Export the shared semantic SVG sprite as per-icon SVG files for native toolkits."""
import argparse
import copy
import json
from pathlib import Path
import xml.etree.ElementTree as ET

NS = "{http://www.w3.org/2000/svg}"
ET.register_namespace("", "http://www.w3.org/2000/svg")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sprite", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    sprite_path, manifest_path, output = Path(args.sprite), Path(args.manifest), Path(args.output)
    sprite = ET.parse(sprite_path).getroot()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    symbols = {node.attrib.get("id", ""): node for node in sprite.findall(f"{NS}symbol")}
    defs = sprite.find(f"{NS}defs")
    output.mkdir(parents=True, exist_ok=True)
    written = []
    for app in manifest.get("apps", []):
        icon_id = app["id"]
        symbol = symbols.get(f"app-{icon_id}")
        if symbol is None:
            raise SystemExit(f"missing SVG symbol for manifest icon: {icon_id}")
        root = ET.Element(f"{NS}svg", {"width": "64", "height": "64", "viewBox": symbol.attrib.get("viewBox", "0 0 64 64")})
        if defs is not None:
            root.append(copy.deepcopy(defs))
        for child in list(symbol):
            root.append(copy.deepcopy(child))
        target = output / f"{icon_id}.svg"
        ET.ElementTree(root).write(target, encoding="utf-8", xml_declaration=True)
        written.append(icon_id)
    if len(written) != int(manifest.get("count", len(written))):
        raise SystemExit(f"icon count mismatch: exported {len(written)}, manifest says {manifest.get('count')}")
    (output / "icon-index.json").write_text(json.dumps({"schema": "CHM-SEMANTIC-ICON-FILES-1", "count": len(written), "icons": written}, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(written)} semantic SVG icons to {output}")

if __name__ == "__main__":
    main()
