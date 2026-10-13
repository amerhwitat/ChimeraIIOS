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
    """Validate the source-discovery index without promoting candidates to ISA forms."""
    db = load(ISA_DB, None)
    if not isinstance(db, dict) or not isinstance(db.get("architectures"), list) or not isinstance(db.get("instructions"), list):
        raise SystemExit(f"Invalid canonical ISA database: {ISA_DB}")
    idx = load(ISA_INDEX, None)
    if idx is None:
        print(f"[ISA] source-discovery index missing; canonical ISA database left unchanged: {ISA_INDEX}")
        return
    if not isinstance(idx, dict) or not isinstance(idx.get("sources", []), list):
        raise SystemExit(f"Invalid online ISA discovery index: {ISA_INDEX}")
    sources = idx.get("sources", [])
    successful = sum(1 for row in sources if isinstance(row, dict) and row.get("status") == "ok")
    candidates = sum(
        len(row.get("definition_identifiers", []))
        for row in sources if isinstance(row, dict) and isinstance(row.get("definition_identifiers", []), list)
    )
    # Keep discovery metadata in its own index. Candidate identifiers are not
    # architecture instruction forms and must not be inserted into the verified
    # encoder/decoder database without per-form validation.
    print(f"[ISA] source discovery: {successful}/{len(sources)} sources available; {candidates} candidate identifiers; canonical forms unchanged")


def merge_commands():
    """Merge discovered command names and source URLs without claiming executability."""
    idx = load(COMMAND_INDEX, None)
    if idx is None:
        print(f"[COMMANDS] source index missing; existing command catalog preserved: {COMMAND_INDEX}")
        return
    if not isinstance(idx, dict):
        raise SystemExit(f"Invalid online command index: {COMMAND_INDEX}")
    source_rows = idx.get("sources", [])
    command_rows = idx.get("commands", [])
    if not isinstance(source_rows, list) or not isinstance(command_rows, list):
        raise SystemExit(f"Invalid online command index schema: {COMMAND_INDEX}")

    db = load(COMMAND_DB, {"schema_version": "1.0", "platforms": {}})
    if not isinstance(db, dict):
        raise SystemExit(f"Invalid command catalog: {COMMAND_DB}")
    platforms = db.setdefault("platforms", {})
    if not isinstance(platforms, dict):
        raise SystemExit(f"Invalid platforms map in command catalog: {COMMAND_DB}")

    additions = 0
    def append_reference(platform_name, item, fallback_url=""):
        nonlocal additions
        name = str(item.get("name", item.get("command", ""))).strip()
        if not name:
            return
        platform = str(item.get("platform", platform_name or "unknown")).strip() or "unknown"
        key = re.sub(r"[^a-z0-9_+-]+", "_", platform.casefold()).strip("_") or "unknown"
        bucket = platforms.setdefault(key, {"platform": platform, "commands": []})
        if not isinstance(bucket, dict):
            raise SystemExit(f"Invalid platform catalog '{key}' in {COMMAND_DB}")
        commands = bucket.setdefault("commands", [])
        if not isinstance(commands, list):
            raise SystemExit(f"Invalid command list for platform '{key}' in {COMMAND_DB}")
        urls = item.get("source_urls")
        if not isinstance(urls, list):
            urls = [item.get("url", item.get("source", fallback_url))]
        urls = [str(url).strip() for url in urls if str(url or "").strip()]
        if not urls:
            urls = [""]
        existing = {
            (str(row.get("name", "")).casefold(), str(row.get("source", "")))
            for row in commands if isinstance(row, dict)
        }
        for url in urls:
            pair = (name.casefold(), url)
            if pair in existing:
                continue
            commands.append({
                "name": name,
                "platform": key,
                "source": url,
                "source_kind": "online-reference-discovery",
                "arabic_alias": item.get("arabic_alias"),
                "translation_status": str(item.get("translation_status", "untranslated")),
                "provider_status": "unverified"
            })
            existing.add(pair)
            additions += 1
        commands.sort(key=lambda row: (str(row.get("name", "")).casefold(), str(row.get("source", ""))))
        bucket["command_count"] = len(commands)

    for source in source_rows:
        if not isinstance(source, dict):
            continue
        platform = str(source.get("platform", source.get("id", "unknown")))
        fallback_url = str(source.get("url", ""))
        source_commands = source.get("commands", [])
        if not isinstance(source_commands, list):
            continue
        for item in source_commands:
            if isinstance(item, dict):
                append_reference(platform, item, fallback_url)
    for item in command_rows:
        if isinstance(item, dict):
            append_reference(str(item.get("platform", "unknown")), item)

    db["generated_at_utc"] = STAMP
    db["online_source_count"] = len(source_rows)
    write(COMMAND_DB, db)
    print(f"[COMMANDS] appended {additions} source-backed command references across {len(platforms)} platform catalogs")

def main():
    merge_isa()
    merge_commands()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
