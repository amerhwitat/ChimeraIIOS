import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_catalog_and_providers():
    catalog = json.loads((ROOT / 'catalog/apps.json').read_text(encoding='utf-8'))
    providers = json.loads((ROOT / 'providers/providers.json').read_text(encoding='utf-8'))
    provider_ids = {p['id'] for p in providers['providers']}
    assert catalog['apps']
    for app in catalog['apps']:
        assert app['id']
        assert app['name']
        assert app['architectures']
        assert app['install']
        assert app['provider'] in provider_ids or app['provider'] in {'external', 'windows-linux', 'web'}


def test_no_binary_payloads_in_catalog():
    catalog = json.loads((ROOT / 'catalog/apps.json').read_text(encoding='utf-8'))
    for app in catalog['apps']:
        assert app.get('source', '').lower().startswith(('http://', 'https://')) or 'source' not in app
