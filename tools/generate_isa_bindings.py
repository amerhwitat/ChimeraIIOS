#!/usr/bin/env python3
"""Generate deterministic language adapters from isa/catalog.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "isa/catalog.json"
OUT = ROOT / "isa/generated"


def main():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    ids = [i["id"] for i in data["instructions"]]
    version = data["schema"]
    (OUT / "isa_catalog.py").write_text(
        f"CATALOG_VERSION = {version!r}\nCATALOG_PATH = 'isa/catalog.json'\nINSTRUCTION_IDS = {ids!r}\n",
        encoding="utf-8")
    ids_json = json.dumps(ids, ensure_ascii=False, separators=(",", ":"))
    (OUT / "isa_catalog.ts").write_text(
        f"export const CATALOG_VERSION = {json.dumps(version)};\nexport const CATALOG_PATH = 'isa/catalog.json';\nexport const INSTRUCTION_IDS = {ids_json} as const;\n",
        encoding="utf-8")
    dart_ids = ", ".join(json.dumps(x) for x in ids)
    (OUT / "isa_catalog.dart").write_text(
        f"const catalogVersion = {json.dumps(version)};\nconst catalogPath = 'isa/catalog.json';\nconst instructionIds = [{dart_ids}];\n",
        encoding="utf-8")
    print(f"generated adapters for {len(ids)} instructions")


if __name__ == "__main__":
    main()
