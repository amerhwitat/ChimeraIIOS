#!/usr/bin/env python3
"""Validate the static boot-stage and artwork contracts without claiming a real boot."""
import base64, hashlib, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def require(condition,message):
    if not condition: raise SystemExit("boot pipeline validation failed: "+message)
def main():
    manifest=json.loads((ROOT/"boot/boot-artwork-manifest.json").read_text())
    menu=json.loads((ROOT/"boot/boot-menu-contract.json").read_text())
    require(manifest.get("schema")=="CHM-BOOT-ARTWORK-3","unknown artwork manifest schema")
    require(menu.get("schema")=="CHM-BOOT-MENU-4","unknown boot menu contract schema")
    expected=["spitfire","jasper","grub","koronos","aurora"]
    chain=manifest.get("boot_chain",{})
    require(all(k in chain for k in expected),"boot chain is missing a required stage")
    require(menu.get("kernel")=="Koronos" and menu.get("primary_loader")=="Spit Fire","boot menu identity mismatch")
    handoff=menu.get("handoff","")
    for stage in ["Spit Fire","Jasper","Koronos","Aurora"]:
        require(stage in handoff,f"canonical handoff omits {stage}")
    for key in expected:
        stage=chain[key]
        require(stage.get("artwork"),f"{key} has no artwork")
        require(stage.get("progress"),f"{key} has no progress contract")
    source=ROOT/"boot/visual/aurora-wayland-glass.jpg.b64"
    require(source.is_file(),"embedded canonical artwork source is missing")
    encoded=re.sub(rb"[^A-Za-z0-9+/=]",b"",source.read_bytes().lstrip(b"\xef\xbb\xbf"))
    candidates=[encoded]
    first_pad=encoded.find(b"=")
    if first_pad>=0:
        end=((first_pad//4)+1)*4
        candidates.append(encoded[:end])
    raw=None
    for candidate in candidates:
        candidate += b"="*((-len(candidate))%4)
        try:
            decoded=base64.b64decode(candidate,validate=False)
        except Exception:
            continue
        if decoded.startswith(bytes.fromhex("ffd8ff")):
            raw=decoded
            break
    require(raw is not None,"embedded artwork payload cannot be decoded as JPEG")
    digest=hashlib.sha256(raw).hexdigest()
    require(digest==manifest.get("embedded_source_sha256"),"embedded artwork checksum mismatch")
    require(raw[:3]==bytes.fromhex("ffd8ff"),"embedded artwork is not a JPEG")
    for rel in manifest.get("sources",[]):
        p=ROOT/rel
        if rel=="boot/visual/aurora-wayland-glass.jpg" and not p.is_file():
            # This raster is intentionally materialized from the tracked .b64 source during ISO staging.
            continue
        require(p.is_file(),f"declared artwork source missing: {rel}")
    for rel in ["boot/spitfire/spitfire-menu.cfg","boot/jasper/jasper.cfg","boot/iso/grub.cfg","boot/jasper/live.cfg","boot/jasper/install.cfg"]:
        p=ROOT/rel
        require(p.is_file(),f"boot menu source missing: {rel}")
        text=p.read_text(errors="replace")
        require("menuentry" in text,f"boot menu has no selectable entries: {rel}")
    # Each stage's static progress contract must be monotonic; progress strings
    # may have textual substeps but cannot go backwards in the canonical map.
    values=[]
    for key in expected:
        rawp=str(chain[key].get("progress",""))
        nums=[int(n) for n in re.findall(r"\d+",rawp)]
        require(nums,f"{key} progress is not machine-readable")
        values.append(nums[0])
    require(values==sorted(values),f"boot progress stages are not monotonic: {values}")
    # Check common menu loops are explicit user-selected return/menu entries;
    # prohibit unconditional top-level configfile chains which can bounce forever.
    for rel in ["boot/spitfire/spitfire-menu.cfg","boot/jasper/jasper.cfg","boot/iso/grub.cfg"]:
        text=(ROOT/rel).read_text(errors="replace")
        depth=0
        for line in text.splitlines():
            s=line.strip()
            if s.startswith("menuentry "): depth+=1
            if s=="}" and depth: depth-=1
            if s.startswith("configfile ") and depth==0:
                raise SystemExit(f"boot pipeline validation failed: top-level configfile loop risk in {rel}: {s}")
    print("boot pipeline contract: PASS (static checks only; no firmware/QEMU boot implied)")
if __name__=="__main__": main()
