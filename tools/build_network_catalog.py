#!/usr/bin/env python3
"""Generate the Network Applications catalogue from one or more repository trees.

Scans for network-facing surfaces (pages, scripts, services, configs, docs) and
classifies them into the categories the desktop panel exposes. The output is a
plain JSON file the shell loads offline; nothing is fetched at runtime.
"""
from __future__ import annotations

import argparse
import json
import os
import re

CATEGORY_RULES = [
    ("monitoring", r"monitor|metrics|telemetry|traffic|dashboard|health|probe|snmp"),
    ("transfer", r"transfer|download|upload|ftp|sftp|rsync|torrent|share|file-drop|copy"),
    ("remote", r"remote|vnc|rdp|ssh|tunnel|teamviewer|desktop-stream|screen-share"),
    ("security", r"security|firewall|vpn|tls|cert|auth|scan|audit|zk-?proof|brute"),
    ("p2p", r"p2p|peer|swarm|mesh|dht|relay"),
    ("cloud", r"cloud|fabric|kubernetes|k8s|aws|azure|gcp|orchestrat|cluster"),
    ("communication", r"voice|call|chat|message|sip|webrtc|rtp|conference|connect"),
    ("emulation", r"emulat|mame|amiga|playstation|retro|rom"),
    ("connectivity", r"network|net-|net_|socket|tcp|udp|http|dns|dhcp|wifi|route|proxy|mqtt|webhook|api|bridge|gateway"),
]

GLYPHS = {
    "monitoring": "📈", "transfer": "⇅", "remote": "🖥", "security": "🛡", "p2p": "🕸",
    "cloud": "☁", "communication": "🎙", "emulation": "🕹", "connectivity": "🌐", "other": "▤",
}

INCLUDE_EXT = {".html", ".js", ".py", ".sh", ".json", ".yaml", ".yml", ".md", ".c", ".cpp", ".conf", ".service"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", "build", ".build", "vendor", "dist", "out",
             "docs", "tests", ".github", "research", "knowledge", "backups", ".chimera-fix-backups"}
SKIP_NAME = re.compile(r"^(__init__|common|base|utils|helpers?|plan|spec|design|readme|changelog|notes|summary|index|manifest|schema)$", re.I)


def classify(text):
    lowered = text.lower()
    for category, pattern in CATEGORY_RULES:
        if re.search(pattern, lowered):
            return category
    return "other"


def pretty_name(stem):
    name = re.sub(r"[_\-]+", " ", stem).strip()
    name = re.sub(r"\s+", " ", name)
    return " ".join(word.capitalize() if word.islower() else word for word in name.split())[:64]


def scan(root, repo_name, limit=400):
    entries = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".chimera")]
        for filename in sorted(filenames):
            stem, ext = os.path.splitext(filename)
            if ext.lower() not in INCLUDE_EXT:
                continue
            if SKIP_NAME.search(stem):
                continue
            rel = os.path.relpath(os.path.join(dirpath, filename), root)
            haystack = rel
            category = classify(haystack)
            if category == "other":
                continue
            # Only keep surfaces that are plausibly applications, not every test fixture.
            if category == "connectivity" and not re.search(r"network|socket|proxy|gateway|dns|dhcp|wifi|http|bridge|api", haystack, re.I):
                continue
            entry_id = re.sub(r"[^a-z0-9]+", "-", rel.lower()).strip("-")[:80]
            entries.append({
                "id": entry_id,
                "name": pretty_name(stem),
                "category": category,
                "glyph": GLYPHS[category],
                "path": rel,
                "entry": rel,
                "repo": repo_name,
                "description": "%s surface found in %s (%s)." % (category.capitalize(), repo_name, rel),
            })
            if len(entries) >= limit:
                return entries
    return entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", action="append", required=True, help="name=path")
    ap.add_argument("--out", required=True)
    ap.add_argument("--merge", action="append", default=[], help="existing catalogue to merge")
    args = ap.parse_args()

    apps = []
    seen = set()
    for item in args.merge:
        if os.path.exists(item):
            data = json.load(open(item, encoding="utf-8"))
            for app in data.get("apps", []):
                if app["id"] not in seen:
                    seen.add(app["id"])
                    apps.append(app)

    for spec in args.repo:
        name, _, path = spec.partition("=")
        for entry in scan(path, name):
            if entry["id"] in seen:
                continue
            seen.add(entry["id"])
            apps.append(entry)

    # Stable ordering: category then name.
    apps.sort(key=lambda item: (item["category"], item["name"].lower()))
    payload = {
        "schema": "aurora-network-apps-1",
        "generated_by": "tools/build_network_catalog.py",
        "count": len(apps),
        "categories": sorted({item["category"] for item in apps}),
        "apps": apps,
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1)
    print("network catalogue: %d entries -> %s" % (len(apps), args.out))


if __name__ == "__main__":
    main()
