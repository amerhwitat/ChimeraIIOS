#!/usr/bin/env python3
"""Validate the evidence-backed Koronos boot map and prevent capability overclaims."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "boot/livecd/boot-sequence.json"

def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    stages = data.get("native_koronos", [])
    numbers = [row.get("stage") for row in stages]
    if numbers != sorted(numbers) or len(numbers) != len(set(numbers)):
        raise SystemExit("native boot stages must be unique and ordered")
    ids = {row.get("id") for row in stages}
    required = {"firmware", "spitfire", "jasper", "grub2", "koronos",
                "initramfs", "ring3-target", "live-target", "kore",
                "display-server", "desktop", "installer", "recovery"}
    if not required.issubset(ids):
        raise SystemExit(f"boot sequence is missing stages: {sorted(required - ids)}")
    missing = []
    for row in stages:
        for rel in row.get("evidence", []):
            path = ROOT / rel
            if not path.exists():
                missing.append(f"{row.get('id')}: {rel}")
    if missing:
        raise SystemExit("boot evidence path missing: " + ", ".join(missing))
    by_id = {row["id"]: row for row in stages}
    expected = {
        "live-target": "interactive-builtins-only",
        "installer": "dry-run-only-no-block-write-backend",
        "recovery": "diagnostics-only-no-repair-backend",
        "display-server": "not-implemented",
        "desktop": "not-yet-runnable-on-native-koronos",
    }
    for key, status in expected.items():
        actual = by_id[key].get("status")
        if actual != status:
            raise SystemExit(f"{key}: expected honest status {status!r}, got {actual!r}")
    hosted = data.get("hosted_linux_desktop", {})
    if hosted.get("status") != "separate-linux-kernel-live-image":
        raise SystemExit("hosted X.Org must remain explicitly separate from Koronos")
    if "X.Org X Server" not in hosted.get("display_servers", []):
        raise SystemExit("hosted Linux X.Org integration missing from boot map")
    arch = {row["arch"]: row["status"] for row in data.get("architecture_status", [])}
    if arch.get("aarch64") != "entry-uart-probe-only-not-full-kernel":
        raise SystemExit("AArch64 probe must not be described as a full Koronos port")
    if arch.get("riscv64") != "entry-uart-probe-only-not-full-kernel":
        raise SystemExit("RV64 probe must not be described as a full Koronos port")
    print(f"Validated {len(stages)} boot stages, {len(arch)} architecture states, and hosted X.Org separation.")
    print("Native installer/recovery/display/desktop gaps remain explicit release gates.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
