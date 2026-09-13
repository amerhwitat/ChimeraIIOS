import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_arabic_locale_is_rtl_and_complete():
    data = json.loads((ROOT / 'desktop/localization/ar-SA.json').read_text(encoding='utf-8'))
    assert data['language'] == 'ar'
    assert data['direction'] == 'rtl'
    required = {'applications','files','settings','network','security','system','terminal','search','shutdown','restart','language','desktop','accessibility'}
    assert required <= set(data['strings'])

def test_desktop_profiles_cover_required_families():
    data = json.loads((ROOT / 'desktop/desktop_profiles.json').read_text(encoding='utf-8'))
    for family in ('linux','windows','macos','chimera'):
        assert data['profiles'][family]
    assert any(p['id'] == 'chimera-arabic' and p['direction'] == 'rtl' for p in data['profiles']['chimera'])

def test_upstream_catalog_is_metadata_only():
    data = json.loads((ROOT / 'desktop/upstream_desktop_catalog.json').read_text(encoding='utf-8'))
    assert data['policy'].startswith('Compatibility metadata only')
    assert {x['family'] for x in data['desktops']} >= {'linux','windows','macos'}
