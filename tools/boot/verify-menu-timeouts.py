#!/usr/bin/env python3
"""Enforce a five-minute, visible, interactive timeout on every GRUB menu, including generated heredocs."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[2])
    args=ap.parse_args()
    root=args.root.resolve()
    failures=[]
    checked=[]
    menu_sources=list((root/"boot").rglob("*.cfg"))
    # Also inspect shell-generated GRUB heredocs (notably the Jasper recovery
    # menu embedded in boot/iso/prepare-layout.sh), which a *.cfg scan misses.
    menu_sources.extend(path for path in (root/"boot").rglob("*.sh")
                        if re.search(r"^\s*menuentry\b", path.read_text(encoding="utf-8",errors="replace"), re.M))
    for path in sorted(set(menu_sources)):
        text=path.read_text(encoding="utf-8",errors="replace")
        if not re.search(r"^\s*menuentry\b",text,re.M):
            continue
        timeout=re.findall(r"^\s*set\s+timeout\s*=\s*(\d+)\s*$",text,re.M)
        style=re.findall(r"^\s*set\s+timeout_style\s*=\s*(\w+)\s*$",text,re.M)
        checked.append(path.relative_to(root).as_posix())
        if not timeout or timeout[-1] != "300":
            failures.append(f"{path.relative_to(root)}: expected set timeout=300")
        if not style or style[-1] != "menu":
            failures.append(f"{path.relative_to(root)}: expected set timeout_style=menu")
    gates=root/"desktop/aurora/gates_menu.json"
    if gates.exists():
        try:
            data=json.loads(gates.read_text(encoding="utf-8"))
            policy=data.get("boot_menu",{})
            if policy.get("timeout_seconds") != 300:
                failures.append("desktop/aurora/gates_menu.json: expected boot_menu.timeout_seconds=300")
            if policy.get("timeout_style") != "menu":
                failures.append("desktop/aurora/gates_menu.json: expected boot_menu.timeout_style=menu")
        except (OSError,json.JSONDecodeError) as exc:
            failures.append(f"desktop/aurora/gates_menu.json: invalid JSON ({exc})")
    else:
        failures.append("desktop/aurora/gates_menu.json: missing")
    protocol=root/"boot/boot_protocol.json"
    if protocol.exists():
        try:
            data=json.loads(protocol.read_text(encoding="utf-8"))
            policy=data.get("menu_first",{})
            if policy.get("timeout_seconds") != 300:
                failures.append("boot/boot_protocol.json: expected menu_first.timeout_seconds=300")
            if policy.get("timeout_style") != "menu":
                failures.append("boot/boot_protocol.json: expected menu_first.timeout_style=menu")
        except (OSError,json.JSONDecodeError) as exc:
            failures.append(f"boot/boot_protocol.json: invalid JSON ({exc})")
    else:
        failures.append("boot/boot_protocol.json: missing")
    builder=root/"live-image/build.sh"
    if builder.exists():
        text=builder.read_text(encoding="utf-8",errors="replace")
        if not re.search(r"set\s+timeout=300",text):
            failures.append("live-image/build.sh: generated GRUB menu must set timeout=300")
        if not re.search(r"set\s+timeout_style=menu",text):
            failures.append("live-image/build.sh: generated GRUB menu must set timeout_style=menu")
    print(f"Checked {len(checked)} GRUB menu configuration files")
    for item in checked: print(f"  PASS {item}")
    if failures:
        for item in failures: print(f"  FAIL {item}",file=sys.stderr)
        return 1
    print("PASS: all boot menus wait 300 seconds in visible menu mode before the default is selected")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
