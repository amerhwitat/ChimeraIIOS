#!/usr/bin/env python3
"""Load isa/isa_database.json into a SQLite database using isa/isa_database.sql."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(json_path: Path, schema_path: Path, output: Path) -> None:
    db = json.loads(json_path.read_text(encoding="utf-8"))
    con = sqlite3.connect(output)
    try:
        con.executescript(schema_path.read_text(encoding="utf-8"))
        con.executemany(
            "INSERT OR REPLACE INTO architectures VALUES (?,?,?,?,?,?,?,?)",
            db["architectures"],
        )
        con.executemany(
            "INSERT OR REPLACE INTO sources VALUES (?,?,?)",
            [(s["id"], s["name"], s["url"]) for s in db["sources"]],
        )
        con.executemany(
            "INSERT OR REPLACE INTO instructions VALUES (?,?,?,?,?,?,?,?)",
            [(r[0], r[1], r[2], json.dumps(r[3]), r[4], r[5], r[6], r[7]) for r in db["instructions"]],
        )
        con.commit()
    finally:
        con.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "isa" / "isa.db"))
    args = parser.parse_args()
    load(ROOT / "isa" / "isa_database.json", ROOT / "isa" / "isa_database.sql", Path(args.output))
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
