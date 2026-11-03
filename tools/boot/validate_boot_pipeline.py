#!/usr/bin/env python3
"""Validate static boot-stage and artwork contracts without claiming a real boot."""
import base64, hashlib, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def require(condition,message):
    if not condition: raise SystemExit("boot pipeline validation failed: "+message)
def main():
    manifest=json.loads((ROOT/"boot/boot-artwork-manifest.json").read_text())
    menu=json.loads((ROOT/"boot/boot-menu-contract.json").read_text())
    require(manifest.get("schema")=="CHM-BOOT-ARTWORK-3","unknown artwork manifest schema")
    require(menu.get("schema") in {"CHM-BOOT-MENU-5","CHM-BOOT-MENU-6"},"unknown boot menu contract schema")
    expected=["firmware","grub","spitfire","gates","jasper","menus","koronos","aurora"]
    chain=manifest.get("boot_chain",{})
    require(list(chain)==expected,"boot chain order must be firmware -> GRUB2 -> Spit Fire -> Jasper -> menus -> Koronos -> Aurora")
    require("Koronos" in menu.get("kernel","") and "Linux Live" in menu.get("kernel","") and menu.get("primary_loader")=="GRUB2 BIOS/UEFI El Torito","boot menu identity mismatch")
    require(menu.get("policy_menu")=="Gates" and menu.get("firmware_menu") in {"Spit Fire","Gates"},"Spit Fire/Gates menu identity mismatch")
    require(menu.get("menu_manager")=="Jasper" and menu.get("policy_menu")=="Gates","Jasper/Gates menu identity mismatch")
    handoff=menu.get("handoff","")
    for stage in ["GRUB2","Spit Fire","Gates","Jasper","Koronos","Aurora"]:
        require(stage in handoff,f"canonical handoff omits {stage}")
    for key in expected:
        stage=chain[key]
        require(stage.get("artwork"),f"{key} has no artwork")
        require(stage.get("event"),f"{key} has no observed-event contract")
        require("progress" not in stage,f"{key} must not claim synthetic progress")
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
        try: decoded=base64.b64decode(candidate,validate=False)
        except Exception: continue
        if decoded.startswith(bytes.fromhex("ffd8ff")):
            raw=decoded
            break
    require(raw is not None,"embedded artwork payload cannot be decoded as JPEG")
    digest=hashlib.sha256(raw).hexdigest()
    require(digest==manifest.get("embedded_source_sha256"),"embedded artwork checksum mismatch")
    for rel in manifest.get("sources",[]):
        p=ROOT/rel
        if rel=="boot/visual/aurora-wayland-glass.jpg" and not p.is_file():
            continue
        require(p.is_file(),f"declared artwork source missing: {rel}")
    for rel in ["boot/spitfire/spitfire-menu.cfg","boot/gates/gates-menu.cfg","boot/jasper/live-image.cfg","boot/jasper/install.cfg","boot/jasper/recovery.cfg"]:
        p=ROOT/rel
        require(p.is_file(),f"boot menu source missing: {rel}")
        text=p.read_text(errors="replace")
        require("menuentry" in text,f"boot menu has no selectable entries: {rel}")
        require(not re.search(r"\b(?:25|40|50|60|75|90|100)%",text),f"{rel} contains synthetic progress percentages")
    root_grub=(ROOT/"boot/iso/grub.cfg").read_text(errors="replace")
    require("configfile /boot/spitfire/spitfire-menu.cfg" in root_grub,"GRUB2 root must hand off to Spit Fire")
    gates=(ROOT/"boot/gates/gates-menu.cfg").read_text(errors="replace")
    require("configfile /boot/jasper/live-image.cfg" in gates,"Gates must hand off to Jasper")
    spit=(ROOT/"boot/spitfire/spitfire-menu.cfg").read_text(errors="replace")
    gates=(ROOT/"boot/gates/gates-menu.cfg").read_text(errors="replace")
    require("configfile /boot/gates/gates-menu.cfg" in spit,"Spit Fire must hand off to Gates")
    require("configfile /boot/jasper/live-image.cfg" in gates,"Gates must hand off to Jasper")
    install=(ROOT/"boot/jasper/install.cfg").read_text(errors="replace")
    recovery=(ROOT/"boot/jasper/recovery.cfg").read_text(errors="replace")
    require("native-installer-runtime.ready" in install,"native Installer must require a ready marker")
    require("native-recovery-runtime.ready" in recovery,"native Recovery must require a ready marker")
    allowed_configfiles={
        "boot/spitfire/spitfire-menu.cfg": ["/boot/gates/gates-menu.cfg"],
        "boot/gates/gates-menu.cfg": ["/boot/jasper/live-image.cfg","/boot/spitfire/spitfire-menu.cfg"],
        "boot/jasper/live-image.cfg": ["/boot/jasper/install.cfg","/boot/jasper/recovery.cfg","/boot/gates/gates-menu.cfg"],
    }
    for rel,targets in allowed_configfiles.items():
        text=(ROOT/rel).read_text(errors="replace")
        for line in text.splitlines():
            item=line.strip()
            if item.startswith("configfile "):
                require(any(target in item for target in targets),f"unexpected menu handoff in {rel}: {item}")
    print("boot pipeline contract: PASS (static checks only; no firmware/QEMU boot implied)")
if __name__=="__main__": main()
