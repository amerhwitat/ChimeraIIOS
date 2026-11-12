#!/usr/bin/env python3
"""Exact-profile Fastboot deployment for Chimera Mobile.

All checks run before the first partition write. The device must already be
OEM-unlocked; this program never unlocks, erases, or bypasses verified boot.
"""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

def run(args, *, check=False, timeout=60):
    return subprocess.run(args, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, check=check, timeout=timeout)

def main(report_path: str) -> int:
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    target = report.get("target", {})
    props = target.get("properties", {})
    serial = target.get("serial")
    profile = report.get("profile", {})
    match = profile.get("match", {})
    security = profile.get("security", {})
    flash = profile.get("flash", {})
    if not serial:
        raise SystemExit("No exact Android serial in build report.")
    if profile.get("support_status") != "hardware-validated":
        raise SystemExit("Profile is not hardware-validated; refusing device writes.")
    if flash.get("method") != "fastboot-profiled":
        raise SystemExit("No approved Fastboot adapter exists for this exact device profile.")
    if security.get("unlockRequired") and props.get("locked") != "0":
        raise SystemExit("Bootloader is not confirmed unlocked; no unlock bypass is attempted.")
    if security.get("unlockRequired") and props.get("vbmeta_device_state") != "unlocked":
        raise SystemExit("Verified Boot state does not confirm an already-unlocked device.")
    identity = (("manufacturer", "manufacturer"), ("model", "model"),
                ("device", "device"), ("board", "board"))
    if not all(match.get(k) and str(match[k]).strip().lower() == str(props.get(v, "")).strip().lower()
               for k, v in identity):
        raise SystemExit("Exact device identity changed or no longer matches the profile.")

    parts = flash.get("partitions", [])
    if not parts or len(parts) > 32:
        raise SystemExit("Missing or excessive profile-mapped partition set.")
    for item in parts:
        name = item.get("name", "")
        image = Path(item.get("image", ""))
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise SystemExit("Unsafe or missing profile partition identifier.")
        if not image.is_file():
            raise SystemExit("Missing mapped image: " + str(image))
        digest = hashlib.sha256(image.read_bytes()).hexdigest()
        if digest.lower() != str(item.get("sha256", "")).lower():
            raise SystemExit("SHA-256 mismatch: " + name)

    adb = run(["adb", "devices"], check=True)
    adb_live = [x.split()[0] for x in adb.stdout.splitlines()[1:]
                if len(x.split()) >= 2 and x.split()[1] == "device"]
    if adb_live != [serial]:
        raise SystemExit(f"ADB device set changed; expected only {serial}, found {adb_live}.")
    print("Exact profile:", profile.get("id"), "device:",
          props.get("manufacturer"), props.get("model"), props.get("device"))
    print("Validated partitions:", ", ".join(x["name"] for x in parts))
    if input("Type FLASH CHIMERA to authorize reboot-to-bootloader and profile-mapped writes: ") != "FLASH CHIMERA":
        raise SystemExit("Cancelled.")

    run(["adb", "-s", serial, "reboot", "bootloader"], check=True)
    fastboot_live = []
    for _ in range(45):
        q = run(["fastboot", "devices"])
        fastboot_live = [x.split()[0] for x in q.stdout.splitlines() if x.split()]
        if fastboot_live:
            break
        time.sleep(2)
    if fastboot_live != [serial]:
        raise SystemExit(f"Fastboot device mismatch; expected only {serial}, found {fastboot_live}. No partitions were written.")

    def getvar(key: str) -> str:
        q = run(["fastboot", "-s", serial, "getvar", key])
        if q.returncode:
            raise SystemExit(f"Fastboot could not read {key}: {q.stdout}")
        pattern = r"(?:\(bootloader\)\s*)?" + re.escape(key) + r":\s*([^\s]+)"
        found = re.search(pattern, q.stdout, re.I)
        return found.group(1).strip().lower() if found else ""

    product = getvar("product")
    expected = str(match.get("device") or match.get("product") or "").strip().lower()
    if not product or product != expected:
        raise SystemExit(f"Fastboot product mismatch: expected {expected!r}, found {product!r}.")
    unlocked = getvar("unlocked")
    if security.get("unlockRequired") and unlocked not in {"yes", "true", "1"}:
        raise SystemExit("Fastboot did not confirm the bootloader is already unlocked; refusing writes.")

    for item in parts:
        print(f"FLASH {item['name']} <- {item['image']}", flush=True)
        run(["fastboot", "-s", serial, "flash", item["name"], item["image"]], check=True, timeout=300)
    run(["fastboot", "-s", serial, "reboot"], check=True)
    run(["adb", "-s", serial, "wait-for-device"], check=True, timeout=180)
    post = run(["adb", "-s", serial, "shell", "getprop", "ro.product.device"], check=True).stdout.strip().lower()
    if post != expected:
        raise SystemExit(f"Post-flash device identity mismatch: expected {expected}, found {post}.")
    print("CHIMERA DEVICE-SPECIFIC FLASH AND POST-BOOT IDENTITY CHECK PASSED")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: chimera-mobile-fastboot.py BUILD_REPORT.json")
    raise SystemExit(main(sys.argv[1]))
