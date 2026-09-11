from tools.toolchain.validate_registry import load, validate

def test_registry_is_valid():
    validate(load())

def test_core_toolchains_exist():
    data = load()
    ids = {item['id'] for item in data['toolchains']}
    assert {'gnu-binutils', 'gcc', 'llvm', 'qemu'}.issubset(ids)

def test_proprietary_tools_are_external():
    data = load()
    for item in data['toolchains']:
        if item['license'] == 'proprietary-external':
            assert item['redistribution'] == 'external-installation'
