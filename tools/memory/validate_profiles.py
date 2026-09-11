import json
import importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
BUS = ROOT / 'memory' / 'bus-profiles.json'
ISA = ROOT / 'isa' / 'registry.py'
TOOLS = ROOT / 'toolchains' / 'registry.json'
def load_isa():
    spec = importlib.util.spec_from_file_location('chimera_isa_registry', ISA)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ISA_TARGETS
def validate():
    bus = json.loads(BUS.read_text(encoding='utf-8'))
    tools = json.loads(TOOLS.read_text(encoding='utf-8'))
    profiles = {x['architecture'] for x in bus['profiles']}
    tool_ids = {x['id'] for x in tools['toolchains']}
    for target in load_isa():
        assert set(target['toolchains']).issubset(tool_ids), target['name']
        if target.get('bus_profile') is not None:
            assert target['bus_profile'] in profiles, target['name']
if __name__ == '__main__':
    validate()
    print('validated ISA, toolchain and memory-bus metadata')
