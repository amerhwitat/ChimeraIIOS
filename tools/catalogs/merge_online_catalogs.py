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


def _verified_encoding_row_count(db):
    """Count rows with a full-width binary value and fixed-bit mask."""
    count = 0
    for row in db.get("instructions", []) if isinstance(db, dict) else []:
        if not isinstance(row, (list, tuple)) or len(row) != 8:
            continue
        try:
            bits = int(row[5])
        except (TypeError, ValueError):
            continue
        value, mask = row[6], row[7]
        if (
            0 < bits <= 65535
            and isinstance(value, str)
            and isinstance(mask, str)
            and re.fullmatch(r"[01]+", value)
            and re.fullmatch(r"[01]+", mask)
            and len(value) == bits
            and len(mask) == bits
        ):
            count += 1
    return count


def _valid_canonical_db(db):
    return (
        isinstance(db, dict)
        and isinstance(db.get("architectures"), list)
        and bool(db["architectures"])
        and isinstance(db.get("instructions"), list)
        and bool(db["instructions"])
    )


def _database_from_catalog():
    """Reconstruct the legacy positional DB from the checked-in structured catalog.

    Encoding masks are deliberately marked unavailable: the structured catalog
    supplies sample encodings and field descriptions, not a universal fixed-bit
    mask for every instruction form.
    """
    catalog_path = ROOT / "isa/catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(catalog, dict) or catalog.get("schema") != "CHM-ISA-CATALOG-1":
        raise ValueError(f"{catalog_path} is not a supported CHM-ISA-CATALOG-1 catalog")
    families = catalog.get("families")
    instructions = catalog.get("instructions")
    if not isinstance(families, list) or not isinstance(instructions, list) or not families or not instructions:
        raise ValueError(f"{catalog_path} has no families or instructions")

    family_map = {}
    architectures = []
    for family in families:
        if not isinstance(family, dict) or not family.get("id"):
            continue
        family_id = str(family["id"])
        family_map[family_id] = family
        architectures.append([family_id, str(family.get("class", "unknown")), family_id])

    rows = []
    for item in instructions:
        if not isinstance(item, dict):
            continue
        family_id = str(item.get("family", ""))
        encoding = item.get("encoding")
        if family_id not in family_map or not isinstance(encoding, dict):
            continue
        sample = encoding.get("sample")
        if not isinstance(sample, dict) or not isinstance(sample.get("binary"), str):
            continue
        bits = sample["binary"]
        try:
            length = int(encoding.get("length_bits", len(bits)))
            if length <= 0 or len(bits) != length or any(bit not in "01" for bit in bits):
                continue
        except (TypeError, ValueError):
            continue
        operands = item.get("operands", [])
        if not isinstance(operands, list):
            operands = []
        operand_names = [
            str(op.get("name", op.get("kind", "operand"))) if isinstance(op, dict) else str(op)
            for op in operands
        ]
        rows.append([
            family_id,
            str(item.get("mnemonic", "UNKNOWN")),
            str(item.get("id", item.get("mnemonic", "unknown"))),
            operand_names,
            str(item.get("syntax", "")),
            length,
            bits,
            "unavailable: consult isa/catalog.json encoding.fields",
        ])

    if not architectures or not rows:
        raise ValueError(f"Could not reconstruct legacy rows from {catalog_path}")
    return {
        "schema": "CHM-ISA-DB-4",
        "recovered_from": "isa/catalog.json",
        "recovery_note": "Encoding samples were preserved; per-form fixed-bit masks remain unavailable and must not be treated as verified.",
        "architectures": architectures,
        "instructions": rows,
        "online_architecture_candidates": [],
        "online_instruction_candidates": [],
    }


def load_canonical_isa():
    """Load canonical DB; recover valid encoding rows from local or remote Git refs."""
    import subprocess

    local_error = "database file is missing"
    try:
        db = json.loads(ISA_DB.read_text(encoding="utf-8"))
        if _valid_canonical_db(db) and _verified_encoding_row_count(db) > 0:
            return db
        local_error = (
            "database has no verified full-width value/mask rows "
            f"({_verified_encoding_row_count(db)} usable rows)"
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        local_error = str(exc)

    # Prefer the current commit, then known remote refs. This recovers a valid
    # committed database even when the working copy was replaced by catalog-only
    # rows whose masks are explicitly unavailable.
    refs = (
        ("HEAD:isa/isa_database.json", "Git HEAD"),
        ("origin/koronos/elf-smp-acceptance-gate:isa/isa_database.json",
         "origin/koronos/elf-smp-acceptance-gate"),
        ("origin/main:isa/isa_database.json", "origin/main"),
    )
    recovered = None
    source = None
    for git_ref, label in refs:
        try:
            raw = subprocess.check_output(
                ["git", "-C", str(ROOT), "show", git_ref],
                text=True, encoding="utf-8", stderr=subprocess.PIPE,
            )
            candidate = json.loads(raw)
            if (
                _valid_canonical_db(candidate)
                and _verified_encoding_row_count(candidate) > 0
            ):
                recovered, source = candidate, label
                break
        except (
            OSError, UnicodeError, json.JSONDecodeError, ValueError,
            subprocess.CalledProcessError,
        ):
            continue

    if recovered is None:
        # The structured catalog is a deterministic last resort, but it contains
        # worked samples rather than universal fixed-bit masks. Preserve that
        # limitation instead of manufacturing templates.
        try:
            recovered = _database_from_catalog()
            source = "isa/catalog.json (sample-only; masks unavailable)"
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError, KeyError) as exc:
            raise SystemExit(
                f"Invalid canonical ISA database: {ISA_DB} ({local_error}); "
                f"could not recover from Git refs or isa/catalog.json ({exc})."
            ) from exc

    write(ISA_DB, recovered)
    verified = _verified_encoding_row_count(recovered)
    print(
        f"[ISA] repaired canonical database from {source}: "
        f"{len(recovered['architectures'])} architectures, "
        f"{len(recovered['instructions'])} instruction rows, "
        f"{verified} verified encoding templates"
    )
    if verified == 0:
        print(
            "[ISA] warning: only exact worked samples are available; "
            "template masks were not fabricated. Fetch a branch containing "
            "verified isa/isa_database.json rows to restore templates."
        )
    return recovered

def merge_isa():
    db = load_canonical_isa()
    # The canonical CHM-ISA-DB-4 database uses positional rows described by
    # architecture_row/instruction_row. Online discoveries are stored separately
    # so unverified objects can never corrupt the verified encoder/decoder rows.
    architecture_candidates = db.setdefault("online_architecture_candidates", [])
    instruction_candidates = db.setdefault("online_instruction_candidates", [])
    if not isinstance(architecture_candidates, list) or not isinstance(instruction_candidates, list):
        raise SystemExit(f"Invalid online-candidate sections in canonical ISA database: {ISA_DB}")

    index = load(ISA_INDEX, {})
    sources = rows_from_index(index)
    existing_architectures = {
        str(item.get("id", item.get("name", "")) if isinstance(item, dict) else item[0] if isinstance(item, list) and item else item).casefold()
        for item in db.get("architectures", [])
    }
    existing_candidates = {
        (str(item.get("architecture", "")).casefold(),
         str(item.get("mnemonic", "")).casefold(),
         str(item.get("source", "")).casefold())
        for item in instruction_candidates if isinstance(item, dict)
    }
    added_architectures = 0
    added_instructions = 0
    for source in sources:
        architecture = str(source.get("architecture") or source.get("platform") or "online-reference").strip()
        url = str(source.get("url") or source.get("source") or "")
        if architecture and architecture.casefold() not in existing_architectures:
            if not any(str(row.get("name", row.get("id", ""))).casefold() == architecture.casefold()
                       for row in architecture_candidates if isinstance(row, dict)):
                architecture_candidates.append({
                    "name": architecture, "source": url,
                    "status": "candidate", "conformance": "unverified"
                })
                added_architectures += 1
        candidates = source.get("instructions", source.get("candidates", []))
        if not isinstance(candidates, list):
            continue
        for item in candidates:
            if isinstance(item, str):
                mnemonic, item_url, semantic = item.strip(), url, None
            elif isinstance(item, dict):
                mnemonic = str(item.get("mnemonic") or item.get("name") or "").strip()
                item_url = str(item.get("url") or item.get("source") or url)
                semantic = item.get("semantic")
            else:
                continue
            key = (architecture.casefold(), mnemonic.casefold(), item_url.casefold())
            if not mnemonic or key in existing_candidates:
                continue
            row = {
                "architecture": architecture, "mnemonic": mnemonic, "source": item_url,
                "status": "candidate", "encoding_verified": False,
                "execution_verified": False, "conformance": "unverified"
            }
            if semantic:
                row["semantic_candidate"] = semantic
            instruction_candidates.append(row)
            existing_candidates.add(key)
            added_instructions += 1

    db["online_discovery_updated_at_utc"] = STAMP
    db["online_source_count"] = len(sources)
    write(ISA_DB, db)
    print(f"[ISA] appended {added_instructions} unverified instruction candidates and {added_architectures} architecture candidates from {len(sources)} source rows; canonical encoding rows preserved")

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
