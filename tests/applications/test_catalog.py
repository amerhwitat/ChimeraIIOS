from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
def test_catalog_entries_are_sandboxed():
    d=json.loads((ROOT/'applications/catalog.json').read_text())
    assert all(x['sandbox'] for x in d['applications'])
