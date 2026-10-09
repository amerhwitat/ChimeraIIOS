import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def test_open_source_registry_contract():
    d=json.loads((ROOT/'opensource/sources.json').read_text(encoding='utf-8'))
    assert d['schema']=='CHM-OSS-SOURCES-1' and d['sources']
    ids=set()
    for x in d['sources']:
        assert x['id'] not in ids; ids.add(x['id'])
        assert x['upstream'].startswith('https://')
        assert x['spdx'] and x['languages'] and x['platforms']
        assert x['integration'] in {'adapter','reference','fetched','vendored'}
        assert x['security']['execute_on_fetch'] is False

def test_service_registry_contract():
    d=json.loads((ROOT/'services/service_registry.json').read_text(encoding='utf-8'))
    assert d['schema']=='CHM-SERVICE-1'
    ids={x['id'] for x in d['services']}
    assert {'service-manager','network','printing'} <= ids
    for x in d['services']:
        assert x['platforms'] and x['capabilities']
        assert set(x['backends']) >= set(x['platforms'])

def test_application_catalog_contract():
    d=json.loads((ROOT/'applications/catalog.json').read_text(encoding='utf-8'))
    assert d['schema']=='CHM-APP-2' and len(d['applications'])>=8
    for x in d['applications']:
        assert x.get('sandbox'), f"application {x.get('id')} has no sandbox policy"
        if x.get('upstream'):
            assert x['upstream'].startswith('https://')
        if x.get('spdx'):
            assert isinstance(x['spdx'], str) and x['spdx']
        if x.get('integration'):
            assert x['integration'] in {'native','wrapped','fetched','reference','repository-application-center','Aurora Crypto Center'}

def test_python_adapters():
    import sys; sys.path.insert(0,str(ROOT))
    from services.python.chimera_services import ServiceState, can_transition, resolve
    from applications.python.chimera_applications import find
    assert can_transition(ServiceState.INACTIVE,ServiceState.STARTING)
    assert not can_transition(ServiceState.ACTIVE,ServiceState.STARTING)
    assert resolve('network','linux').backend=='networkmanager'
    assert resolve('printing','windows').backend=='spooler'
    assert any(x['id']=='libreoffice' for x in find('office','linux'))
    assert any(x['id']=='terminal' for x in find('terminal','windows'))
