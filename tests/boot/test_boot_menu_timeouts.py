#!/usr/bin/env python3
"""Contract test for long interactive Jasper/Gates/GRUB boot menus."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"vendor/chimera-ii-os/source" if (ROOT/"vendor/chimera-ii-os/source").is_dir() else ROOT
BOOT=SOURCE/"boot"
PRIMARY=("iso/grub.cfg","jasper/jasper.cfg","spitfire/spitfire-menu.cfg","loader-menu.cfg")
SUBMENUS=("installation/menu.cfg","installation/services.cfg","jasper/diagnostics.cfg","jasper/install.cfg",
          "jasper/last-known-good.cfg","jasper/live.cfg","jasper/recovery.cfg","jasper/retro.cfg","jasper/safe-mode.cfg")
def timeout(path):
    text=path.read_text(encoding="utf-8")
    match=re.search(r"^\s*set timeout=(\d+)\s*$",text,re.M)
    assert match, f"{path}: no explicit GRUB timeout"
    assert re.search(r"^\s*set timeout_style=menu\s*$",text,re.M), f"{path}: timeout_style must remain menu"
    return int(match.group(1))
for rel in PRIMARY:
    actual=timeout(BOOT/rel)
    assert actual==300, f"{rel}: expected 300 seconds, got {actual}"
for rel in SUBMENUS:
    actual=timeout(BOOT/rel)
    assert actual==120, f"{rel}: expected 120 seconds, got {actual}"
contract=json.loads((BOOT/"boot-menu-contract.json").read_text())
assert contract["timeouts"]=={"primary_seconds":300,"submenu_seconds":120,"default_entry":"live","policy":"Wait for user input for five minutes on primary boot menus and two minutes on nested menus, then select the configured default entry."}
gates=json.loads((SOURCE/"desktop/aurora/gates_menu.json").read_text())
interaction=gates["interaction"]; boot=gates["boot_contract"]
assert interaction["auto_launch_default"] is True
assert interaction["idle_default_timeout_seconds"]==300
assert interaction["menu_remains_open_until_user_action"] is False
assert boot["primary_menu_timeout_seconds"]==300 and boot["submenu_timeout_seconds"]==120
assert boot["default_action"]=="live"
print("PASS: primary menus wait 300 seconds; nested menus wait 120 seconds; Gates default action is live.")
