#!/usr/bin/env python3
"""Merge source-backed online ISA and command discoveries into their own catalogs.

Discovered identifiers are candidates only: this tool does not assert that an
ISA encoding executes, that an architecture is conformant, or that a command is
installed. Missing optional online indexes are treated as empty inputs.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISA_DB = ROOT / "isa/isa_database.json"
ISA_INDEX = ROOT / "data/isa/online-isa-index.json"
COMMAND_INDEX = ROOT / "system/commands/online-command-catalog.json"
COMMAND_DB = ROOT / "system/commands/ss64-command-catalog.json"
STAMP = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def write(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    json.loads(tmp.read_text(encoding="utf-8"))
    tmp.replace(path)


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", str(value).casefold()).strip("-") or "unknown"


def rows_from_index(index):
    """Accept either a {sources:[...]} index or a flat {commands:[...]} index."""
    if not isinstance(index, dict):
        return []
    sources = index.get("sources")
    if isinstance(sources, list):
        return [row for row in sources if isinstance(row, dict)]
    commands = index.get("commands")
    if isinstance(commands, list):
        return [{"platform": "online-reference", "url": "", "commands": commands}]
    return []


def merge_isa():
    db = load(ISA_DB, None)
    if not isinstance(db, dict):
        raise SystemExit(f"Invalid canonical ISA database: {ISA_DB}")
    architectures = db.setdefault("architectures", [])
    instructions = db.setdefault("instructions", [])
    if not isinstance(architectures, list) or not isinstance(instructions, list):
        raise SystemExit(f"Invalid canonical ISA database schema: {ISA_DB}")

    index = load(ISA_INDEX, {})
    sources = rows_from_index(index)
    existing = {
        (str(item.get("architecture", "")).casefold(), str(item.get("mnemonic", "")).casefold(),
         str(item.get("source", "")).casefold())
        for item in instructions if isinstance(item, dict)
    }
    added = 0
    for source in sources:
        architecture = str(source.get("architecture") or source.get("platform") or "online-reference").strip()
        url = str(source.get("url") or source.get("source") or "")
        if architecture and architecture.casefold() not in {
            str(a.get("name", a.get("id", "")) if isinstance(a, dict) else a).casefold()
            for a in architectures
        }:
            architectures.append({"name": architecture, "source": url,
                                  "status": "candidate", "conformance": "unverified"})
        candidates = source.get("instructions", source.get("candidates", []))
        if not isinstance(candidates, list):
            continue
        for item in candidates:
            if isinstance(item, str):
                mnemonic, item_url = item.strip(), url
                semantic = None
            elif isinstance(item, dict):
                mnemonic = str(item.get("mnemonic") or item.get("name") or "").strip()
                item_url = str(item.get("url") or item.get("source") or url)
                semantic = item.get("semantic")
            else:
                continue
            key = (architecture.casefold(), mnemonic.casefold(), item_url.casefold())
            if not mnemonic or key in existing:
                continue
            row = {"architecture": architecture, "mnemonic": mnemonic, "source": item_url,
                   "status": "candidate", "encoding_verified": False,
                   "execution_verified": False, "conformance": "unverified"}
            if semantic:
                row["semantic_candidate"] = semantic
            instructions.append(row)
            existing.add(key)
            added += 1
    db["online_discovery_updated_at_utc"] = STAMP
    db["online_source_count"] = len(sources)
    write(ISA_DB, db)
    print(f"[ISA] appended {added} source-backed instruction candidates from {len(sources)} source rows")


def merge_commands():
    index = load(COMMAND_INDEX, {})
    sources = rows_from_index(index)
    db = load(COMMAND_DB, {})
    if not isinstance(db, dict):
        raise SystemExit(f"Invalid command catalog: {COMMAND_DB}")
    platforms = db.setdefault("platforms", {})
    if not isinstance(platforms, dict):
        raise SystemExit(f"Invalid command catalog platform map: {COMMAND_DB}")

    added = 0
    for source in sources:
        platform = str(source.get("platform") or source.get("name") or "online-reference").strip()
        key = re.sub(r"[^a-z0-9_+-]+", "_", platform.casefold()).strip("_") or "online_reference"
        bucket = platforms.setdefault(key, {"index": str(source.get("url") or ""), "commands": []})
        if not isinstance(bucket, dict):
            continue
        commands = bucket.setdefault("commands", [])
        if not isinstance(commands, list):
            continue
        existing = {
            (str(row.get("name", "")).casefold(), str(row.get("source", "")).casefold())
            for row in commands if isinstance(row, dict)
        }
        items = source.get("commands", [])
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, str):
                name, url = item.strip(), str(source.get("url") or "")
            elif isinstance(item, dict):
                name = str(item.get("name") or item.get("command") or "").strip()
                url = str(item.get("url") or item.get("source") or source.get("url") or "")
            else:
                continue
            pair = (name.casefold(), url.casefold())
            if not name or pair in existing:
                continue
            commands.append({"name": name, "platform": key, "source": url,
                             "source_kind": "online-reference-discovery",
                             "arabic_alias": None, "translation_status": "untranslated",
                             "provider_status": "unverified"})
            existing.add(pair)
            added += 1
        commands.sort(key=lambda row: (str(row.get("name", "")).casefold(),
                                       str(row.get("source", "")).casefold()))
        bucket["command_count"] = len(commands)
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
