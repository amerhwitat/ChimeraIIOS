from pathlib import Path
import importlib.util

ROOT = Path(__file__).parents[2]

def load(path):
    spec = importlib.util.spec_from_file_location('isa_registry', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_isa_registry_exposes_native_and_compatibility_targets():
    mod = load(ROOT / 'isa' / 'registry.py')
    names = {x['name'] for x in mod.ISA_TARGETS}
    assert {'chimera-r8192','chimera-c8192','x86-64','aarch64','riscv64','power64','mips64','sparc64'} <= names

def test_registern_compatible_native_widths_are_declared():
    mod = load(ROOT / 'isa' / 'registry.py')
    assert next(x for x in mod.ISA_TARGETS if x['name'] == 'chimera-r8192')['width'] == 8192
