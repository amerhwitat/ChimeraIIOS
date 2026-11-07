#!/usr/bin/env python3
"""Export Aurora's compiled-in SVG icon catalogue as installable hicolor assets."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",type=Path,default=ROOT/"desktop/aurora/icons/chimera_icons.cpp")
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    source=args.source.read_text(encoding="utf-8")
    pattern=re.compile(r'\{"([^"]+)","(<svg[\s\S]*?</svg>)"\}')
    icons=pattern.findall(source)
    if not icons:
        raise SystemExit("no embedded Aurora SVG icons found; refusing to emit an empty theme")
    args.output.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for name,svg in icons:
        if "<svg" not in svg or "</svg>" not in svg:
            raise SystemExit(f"invalid SVG source for icon {name}")
        target=args.output/f"chimera-{name}.svg"
        target.write_text(svg+"\n",encoding="utf-8")
        manifest.append({"name":name,"file":target.name,"source":"desktop/aurora/icons/chimera_icons.cpp"})
    (args.output/"index.theme").write_text(
        "[Icon Theme]\nName=Chimera Aurora\nComment=Native Aurora application icons\nDirectories=scalable/apps\n\n"
        "[scalable/apps]\nSize=48\nType=Scalable\nMinSize=16\nMaxSize=256\n",encoding="utf-8")
    (args.output/"manifest.json").write_text(json.dumps({
        "schema":"CHIMERA-AURORA-ICON-EXPORT-1","count":len(manifest),"icons":manifest
    },indent=2)+"\n",encoding="utf-8")
    print(f"Exported {len(manifest)} Aurora SVG icons to {args.output}")
if __name__=="__main__": main()
