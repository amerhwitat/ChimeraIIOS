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
    sources = idx.get("sources", []) if isinstance(idx, dict) else []
    families = {str(row[2]).casefold() for row in db["architectures"] if isinstance(row, list) and len(row) >= 3}
    added = []
    for src in sources:
        family = str(src.get("family", "")).strip()
        if family and family.casefold() not in families:
            added.append([slug(family), "catalog-only", family, 0, "catalog-only",
                          "Discovered from online source index; ISA class/width/encodings unverified",
                          str(src.get("id", "online-discovery")), 0])
            families.add(family.casefold())
    if added:
        db["architectures"].extend(added)
    # Keep source discoveries separate from executable instruction forms.
    old = db.get("online_discovery", {})
    prior_sources = {str(x.get("id")): x for x in old.get("sources", [])} if isinstance(old, dict) else {}
    for src in sources:
        prior_sources[str(src.get("id", src.get("url", "unknown")))] = {
            "id": src.get("id"), "family": src.get("family"), "url": src.get("url"),
            "authority": src.get("authority"), "status": src.get("status", "indexed"),
            "checked_utc": src.get("checked_utc"), "sha256": src.get("sha256"),
            "definition_identifier_count": src.get("definition_identifier_count", 0),
            "definition_identifiers": src.get("definition_identifiers", []),
            "coverage_note": "Discovery candidates only; no encoding, decoder, execution, or conformance claim."
        }
    db["online_discovery"] = {
        "updated_utc": STAMP,
        "policy": "Source URLs and identifiers are discovery metadata. Only independently verified encodings belong in instructions.",
        "sources": sorted(prior_sources.values(), key=lambda x: str(x.get("id", ""))),
        "candidate_definition_count": sum(len(x.get("definition_identifiers", [])) for x in prior_sources.values()),
    }
    db["version"] = str(db.get("version", "2026.10")) + "+online-index"
    write(ISA_DB, db)
    print(f"[ISA] appended {len(added)} catalog-only architecture families; indexed {len(sources)} source records; executable instruction rows unchanged")

def merge_commands():
    idx = load(COMMAND_INDEX, {})
    if not isinstance(idx, dict):
        print("[COMMANDS] no online command index; skipping")
        return
    db = load(COMMAND_DB, {})
    if not isinstance(db, dict):
        db = {}
    db.setdefault("schema_version", "4.5")
    db.setdefault("product", "Chimera II OS")
    db.setdefault("source", "SS64 plus official command references")
    db.setdefault("source_index", "https://ss64.com/")
    db.setdefault("policy", "Names, source URLs, and curated aliases only; reference prose is not mirrored and discovered names are not proof of executable providers.")
    platforms = db.setdefault("platforms", {})
    sources = idx.get("sources", [])
    added = 0
    for src in sources:
        platform = str(src.get("platform", "online-reference")).strip() or "online-reference"
        key = re.sub(r"[^a-z0-9_+-]+", "_", platform.casefold()).strip("_") or "online_reference"
        bucket = platforms.setdefault(key, {"index": (src.get("url") or (src.get("source_urls") or [""])[0]), "commands": []})
        existing = {(str(x.get("name", "")).casefold(), str(x.get("source", ""))) for x in bucket.get("commands", [])}
        urls = src.get("source_urls", [])
        name = str(src.get("name", "")).strip()
        if not name:
            continue
        for url in urls or [src.get("url", "")]:
            url = str(url or "")
            pair = (name.casefold(), url)
            if pair in existing:
                continue
            bucket.setdefault("commands", []).append({
                "name": name, "platform": key, "source": url,
                "source_kind": "online-reference-discovery",
                "arabic_alias": src.get("arabic_alias"),
                "translation_status": src.get("translation_status", "untranslated"),
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
