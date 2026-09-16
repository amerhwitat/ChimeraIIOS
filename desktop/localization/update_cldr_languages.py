#!/usr/bin/env python3
"""Refresh Aurora's language/script registry from Unicode CLDR.

The OS stores a compact policy file in-repo and can refresh the detailed
language inventory at build time. Network retrieval is explicit: this script
never executes downloaded content.
"""
from __future__ import annotations
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "cldr_language_inventory.json"
URL = "https://raw.githubusercontent.com/unicode-org/cldr-json/main/cldr-json/cldr-core/likelySubtags.json"


def main() -> None:
    req = urllib.request.Request(URL, headers={"User-Agent": "Chimera-II-OS-language-updater/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.load(response)
    likely = data.get("main", {}).get("en", {}).get("identity", {})
    payload = {
        "schema": "chimera.cldr-language-inventory.v1",
        "source": URL,
        "source_note": "CLDR likelySubtags is used as a machine-readable locale/script seed; detailed translations and locale data remain in CLDR packages.",
        "cldr": data,
        "identity": likely,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
