from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
def test_service_registry_has_required_backends():
    d=json.loads((ROOT/'services/service_registry.json').read_text())
    for item in d['services']:
        assert set(item['platforms']) <= set(item['backends'])
