#!/usr/bin/env python3
"""Import cross-OS command names as evidence-tagged candidates, never as fake binaries."""
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "system/commands/chimera-command-list.json"
DEFAULT_SS64 = ROOT / "system/commands/ss64-command-catalog.json"
DEFAULT_ARABIC = ROOT / "system/commands/ss64-command-catalog.ar.json"
DEFAULT_OUT = ROOT / "system/commands/native-command-candidates.json"
NATIVE = {"pwd", "echo", "ls", "cp", "mv", "touch", "mkdir", "rm", "cat", "clear", "whoami", "hostname", "date", "true", "false"}
COMMON = {"pwd","echo","ls","cp","mv","touch","mkdir","rm","cat","clear","whoami","hostname","date","true","false","printf","grep","find","head","tail","sort","wc","cut","tr","env","uname","id","ps","kill","chmod","chown","df","du","mount","umount","tar","gzip","sha256sum","curl","wget","git","python3","sh","bash","test","help","man","history","cd","exit","read","export","alias","which","command"}
def names(items):
    if not isinstance(items, list): return
    for item in items:
        if isinstance(item, str) and item.strip(): yield item.strip()
        elif isinstance(item, dict) and isinstance(item.get("name"), str) and item["name"].strip(): yield item["name"].strip()
def load(path, default):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): return default
def build(source, ss64, arabic):
    records = {}
    def add(name, platform, source_url=None):
        key = name.casefold()
        row = records.setdefault(key, {"name": name, "platforms": [], "source_urls": []})
        if platform not in row["platforms"]: row["platforms"].append(platform)
        if source_url and source_url not in row["source_urls"]: row["source_urls"].append(source_url)
    if isinstance(source, dict):
        for key, value in source.items():
            if isinstance(value, list):
                for name in names(value): add(name, key)
        platforms = source.get("platforms", {})
        for key, value in platforms.items():
            if isinstance(value, dict) and value.get("index"):
                for row in records.values():
                    if key in row["platforms"] and value["index"] not in row["source_urls"]:
                        row["source_urls"].append(value["index"])
    if isinstance(ss64, dict):
        for platform, data in ss64.get("platforms", {}).items():
            for item in data.get("commands", []):
                if isinstance(item, dict) and item.get("name"):
                    add(str(item["name"]).strip(), platform, item.get("source"))
    for name in COMMON: add(name, "common-command-candidate")
    for name in NATIVE: add(name, "chimera-native-implemented")
    labels = {}
    if isinstance(arabic, dict): labels = arabic.get("commands", {})
    for key, value in labels.items():
        name = value.get("name", key) if isinstance(value, dict) else key
        if name: add(str(name), "arabic-command-catalog")
    commands = []
    for key, row in sorted(records.items()):
        native = key in NATIVE
        commands.append({
            "name": row["name"], "normalized_name": key,
            "platforms": sorted(row["platforms"]),
            "status": "native-implemented" if native else "candidate-only",
            "dispatch": "chimera-cmd" if native else "defer-to-runtime-learning",
            "execution_allowed": native,
            "source_urls": sorted(row["source_urls"]),
            "arabic_label": (labels.get(key, {}).get("label") if isinstance(labels.get(key), dict) else None),
            "learning": None if native else {
                "state": "unresolved",
                "queue": "runtime-rnn-command-candidates",
                "policy": "RNN may rank documented providers and request tests; it must not execute unknown commands or invent implementation claims."
            }
        })
    return {
        "schema": "CHM-NATIVE-COMMAND-CANDIDATES-1",
        "generated_by": "tools/commands/import_command_candidates.py",
        "policy": "Catalog import is discovery only. Only the explicit native allowlist is executable here. Candidate entries remain unresolved until a provider is installed and behavior is tested.",
        "native_allowlist": sorted(NATIVE),
        "common_candidates": sorted(COMMON),
        "counts": {"total": len(commands), "native_implemented": sum(x["status"] == "native-implemented" for x in commands), "candidate_only": sum(x["status"] == "candidate-only" for x in commands)},
        "commands": commands
    }
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--ss64", type=Path, default=DEFAULT_SS64)
    ap.add_argument("--arabic", type=Path, default=DEFAULT_ARABIC)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--check", action="store_true")
    a=ap.parse_args()
    data=build(load(a.source, {}), load(a.ss64, {}), load(a.arabic, {}))
    encoded=json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)+"\n"
    if a.check:
        if not a.output.exists() or a.output.read_text(encoding="utf-8") != encoded:
            raise SystemExit("native command candidate catalog is stale; regenerate and commit it")
    else:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(encoded, encoding="utf-8")
    print("Imported command candidates:", json.dumps(data["counts"], sort_keys=True))
if __name__ == "__main__": main()
