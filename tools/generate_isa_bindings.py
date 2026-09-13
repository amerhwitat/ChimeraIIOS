#!/usr/bin/env python3
"""Generate small language adapters from isa/catalog.json.

The canonical ISA facts remain in JSON so operand/encoding updates have one source
of truth; language adapters expose version/path and may load the catalog at runtime.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "isa/catalog.json"
OUT = ROOT / "isa/generated"

TEMPLATES = {
    "python": "CATALOG_VERSION = {version!r}\nCATALOG_PATH = 'isa/catalog.json'\nINSTRUCTION_IDS = {ids!r}\n",
    "typescript": "export const CATALOG_VERSION = {version!r};\nexport const CATALOG_PATH = 'isa/catalog.json';\nexport const INSTRUCTION_IDS = {ids!r} as const;\n",
    "dart": "const catalogVersion = {version!r};\nconst catalogPath = 'isa/catalog.json';\nconst instructionIds = {ids!r};\n",
}

def main():
    data = json.loads(CATALOG.read_text(encoding='utf-8'))
    OUT.mkdir(parents=True, exist_ok=True)
    ids = tuple(i['id'] for i in data['instructions'])
    for lang, template in TEMPLATES.items():
        ext = {'python':'py','typescript':'ts','dart':'dart'}[lang]
        (OUT / f'isa_catalog.{ext}').write_text(template.format(version=data['schema'], ids=ids), encoding='utf-8')
    print(f'generated adapters for {len(ids)} instructions')

if __name__ == '__main__':
    main()
