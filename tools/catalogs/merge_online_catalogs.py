#!/usr/bin/env python3
"""Merge source-backed online ISA/command discovery into Chimera catalogs.

This stores names, URLs, source hashes, and status metadata only. Discovered
instruction identifiers are candidates, not verified encodings or conformance
claims; command names are not installed as executable binaries.
"""
from __future__ import annotations
import hashlib, json, re, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISA_DB = ROOT / "isa/isa_database.json"
ISA_INDEX = ROOT / "data/isa/online-isa-index.json"
COMMAND_INDEX = ROOT / "system/commands/online-command-catalog.json"
COMMAND_DB = ROOT / "system/commands/ss64-command-catalog.json"
STAMP = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    json.loads(tmp.read_text(encoding="utf-8"))
    tmp.replace(path)

def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "unknown"

def merge_isa():
    db = load(ISA_DB, None)
    if not isinstance(db, dict) or not isinstance(db.get("architectures"), list) or not isinstance(db.get("instructions"), list):
        raise SystemExit(f"Invalid canonical ISA database: {ISA_DB}")
    idx = load(ISA_INDEX, {})
    sources = idx.get("sources", [])
    platforms = db.setdefault("platforms", {})
    added = 0
    for source_row in sources:
        platform = str(source_row.get("platform", "online-reference")).strip() or "online-reference"
        key = re.sub(r"[^a-z0-9_+-]+", "_", platform.casefold()).strip("_") or "online_reference"
        bucket = platforms.setdefault(key, {"index": source_row.get("url", ""), "commands": []})
        existing = {(str(x.get("name", "")).casefold(), str(x.get("source", ""))) for x in bucket.get("commands", [])}
        for item in source_row.get("commands", []):
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            url = str(item.get("url", source_row.get("url", "")) or "")
            pair = (name.casefold(), url)
            if pair in existing:
                continue
            bucket.setdefault("commands", []).append({
                "name": name, "platform": key, "source": url,
                "source_kind": "online-reference-discovery",
                "arabic_alias": None,
                "translation_status": "untranslated",
                "provider_status": "unverified"
            })
            existing.add(pair); added += 1
        bucket["commands"].sort(key=lambda x: (str(x.get("name", "")).casefold(), str(x.get("source", ""))))
        bucket["command_count"] = len(bucket["commands"])
    db["generated_at_utc"] = STAMP
    db["online_source_count"] = len(sources)
    write(COMMAND_DB, db)
    print(f"[COMMANDS] appended {added} source-backed command references across {len(platforms)} platform catalogs")

def main():
    merge_isa()
    merge_commands()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
