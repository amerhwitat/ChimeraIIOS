#!/usr/bin/env python3
"""Export every embedded Aurora C++ SVG icon into a freedesktop icon theme."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
PATTERN=re.compile(r'\{"([a-zA-Z0-9_-]+)","(<svg[\\s\\S]*?</svg>)"\}')
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--source",type=Path,default=Path("desktop/aurora/icons/chimera_icons.cpp"));ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
    text=a.source.read_text(encoding="utf-8");found=PATTERN.findall(text)
    if not found: raise SystemExit(f"no embedded SVG icons found in {a.source}")
    root=a.output;apps=root/"scalable/apps";apps.mkdir(parents=True,exist_ok=True)
    entries=[]
    for name,svg in found:
        svg=svg.replace("<svg ","<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" fill=\"#dceeff\" ",1)
        (apps/f"chimera-{name}.svg").write_text(svg+"\n",encoding="utf-8")
        entries.append({"id":name,"file":f"scalable/apps/chimera-{name}.svg","source":"desktop/aurora/icons/chimera_icons.cpp"})
    (root/"index.theme").write_text("""[Icon Theme]
Name=Chimera Aurora
Comment=Chimera II OS Aurora SVG icon theme
Inherits=Adwaita,hicolor
Directories=scalable/apps

[scalable/apps]
Size=24
Type=Scalable
MinSize=16
MaxSize=512
Context=Applications
""",encoding="utf-8")
    (a.output/"chimera-aurora-icon-manifest.json").write_text(json.dumps({"schema":"CHM-AURORA-ICON-THEME-1","theme":"chimera-aurora","count":len(entries),"icons":entries},indent=2)+"\n",encoding="utf-8")
    print(f"Exported {len(entries)} embedded Aurora SVG icons to {a.output}")
if __name__=="__main__":main()
