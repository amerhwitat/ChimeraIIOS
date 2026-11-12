#!/usr/bin/env python3
"""Validate Chimera Mobile device-profile structure without implying device support."""
import json
import sys
from pathlib import Path

REQUIRED = {"id", "architecture", "soc", "boot", "partitions", "security", "support_status"}
ARCHES = {"aarch64", "armv7", "x86_64"}
STATUSES = {"reference-only", "bring-up", "hardware-validated"}

def validate(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = REQUIRED - set(data)
    if missing:
        raise SystemExit("missing profile fields: " + ", ".join(sorted(missing)))
    if data["architecture"] not in ARCHES:
        raise SystemExit("unsupported architecture")
    if data["support_status"] not in STATUSES:
        raise SystemExit("invalid support_status")
    if not isinstance(data["partitions"], list) or not data["partitions"]:
        raise SystemExit("partitions must be a non-empty list")
    names = set()
    for part in data["partitions"]:
        name = part.get("name", "")
        if not name or name in names or "/" in name or "\\\\" in name:
            raise SystemExit("invalid or duplicate partition identifier")
        names.add(name)
    security = data["security"]
    if security.get("avb") and not security.get("unlockRequired"):
        raise SystemExit("AVB profile must declare OEM unlock/signing policy")
    if data["support_status"] == "hardware-validated":
        match = data.get("match", {})
        exact_keys = ("manufacturer", "model", "device", "product", "board")
        if not isinstance(match, dict) or not any(match.get(k) for k in exact_keys):
            raise SystemExit("hardware-validated profile requires exact hardware identifiers")
        if not data.get("codename") or not data.get("policy", {}).get("signed_images_required"):
            raise SystemExit("hardware-validated profile requires codename and signed-image policy")
        flash = data.get("flash", {})
        if flash.get("method") not in {"fastboot-profiled", "vendor-signed"} or not flash.get("partitions"):
            raise SystemExit("hardware-validated profile requires an approved device flash adapter")
        bundle = data.get("boot_bundle", {})
        for key in ("boot_image", "vendor_boot_image", "vbmeta_image"):
            if not bundle.get(key):
                raise SystemExit("hardware-validated profile missing boot bundle field: " + key)
    print(f"VALID {data['id']} ({data['architecture']}; {data['support_status']})")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate-profile.py PROFILE.json")
    validate(sys.argv[1])
