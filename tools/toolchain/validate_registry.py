import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / 'toolchains' / 'registry.json'
ALLOWED_KINDS = {'assembler','disassembler','compiler','linker','object-tools','debug-info','debugger','system-emulator','user-emulator','debugger-bridge','disassembler-adjacent'}
def load():
    return json.loads(REGISTRY.read_text(encoding='utf-8'))
def validate(data):
    ids=set()
    for item in data['toolchains']:
        assert item['id'] and item['id'] not in ids
        ids.add(item['id'])
        assert set(item['kind']).issubset(ALLOWED_KINDS)
        assert item['targets'] and 'license' in item and 'detection' in item
    assert {'gnu-binutils','gcc','llvm','qemu'}.issubset(ids)
if __name__ == '__main__':
    validate(load())
    print('validated universal CPU toolchain registry')
