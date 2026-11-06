#!/usr/bin/env python3
"""Export the Aurora app icon SVG sprite as individual hicolor theme icons."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
import xml.etree.ElementTree as ET

SVG = "{http://www.w3.org/2000/svg}"
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--sprite",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    tree=ET.parse(a.sprite); root=tree.getroot()
    defs=root.find(SVG+"defs")
    gradients=list(defs) if defs is not None else []
    symbols=[node for node in root.iter(SVG+"symbol") if node.get("id","").startswith("app-")]
    if not symbols: raise SystemExit("no app-* symbols found in sprite")
    a.output.mkdir(parents=True,exist_ok=True)
    entries=[]
    for symbol in symbols:
        icon_id=symbol.get("id","")[4:]
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*",icon_id):
            raise SystemExit(f"unsafe icon id: {icon_id!r}")
        svg=ET.Element(SVG+"svg",{"viewBox":symbol.get("viewBox","0 0 64 64"),"role":"img","aria-label":icon_id})
        svg_defs=ET.SubElement(svg,SVG+"defs")
        for gradient in gradients:
            svg_defs.append(ET.fromstring(ET.tostring(gradient,encoding="unicode")))
        for child in list(symbol):
            svg.append(ET.fromstring(ET.tostring(child,encoding="unicode")))
        dest=a.output/f"chimera-{icon_id}.svg"
        ET.ElementTree(svg).write(dest,encoding="utf-8",xml_declaration=True)
        entries.append({"id":icon_id,"file":dest.name,"symbol":"#"+symbol.get("id")})
    out={"schema":"chimera-aurora-hicolor-icons/v1","count":len(entries),"icons":entries,
         "source_sprite":str(a.sprite),"source_manifest":str(a.manifest)}
    (a.output/"manifest.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(f"Exported {len(entries)} original Aurora app icons to {a.output}")
if __name__=="__main__": main()
