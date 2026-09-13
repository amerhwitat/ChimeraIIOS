import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_manifest_has_supported_language_lifecycles():
    data = json.loads((ROOT / 'tools/build/build_manifest.json').read_text())
    required = {'python','rust','node','java','dotnet','kotlin','swift','dart','asm'}
    assert required <= set(data['languages'])
    for item in required:
        assert all(data['languages'][item].get(k) for k in ('probe','build','test'))

def test_safety_defaults_are_non_destructive():
    safety = json.loads((ROOT / 'tools/build/build_manifest.json').read_text())['safety']
    assert safety['execute_downloaded_scripts'] is False
    assert safety['kernel_driver_install_default'] is False
    assert safety['firmware_install_default'] is False
    assert safety['destructive_storage_default'] is False
