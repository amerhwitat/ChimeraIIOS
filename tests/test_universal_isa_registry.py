import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("chimera_isa_registry", ROOT / "isa" / "registry.py")
registry = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(registry)


def test_registry_is_unique_and_valid():
    registry.validate_registry()
    names = {target["name"] for target in registry.ISA_TARGETS}
    assert len(names) == len(registry.ISA_TARGETS)
    assert "chimera-r8192" in names
    assert "chimera-c8192" in names


def test_wide_native_targets_are_register_n_compatible():
    for name in ("chimera-r8192", "chimera-c8192"):
        target = registry.find_target(name)
        assert target is not None
        assert target["width"] == 8192
        assert target["execution"] == "native"
        assert "tensor" in target["features"]
        assert "crypto" in target["features"]


def test_foreign_targets_have_explicit_execution_boundary():
    for target in registry.ISA_TARGETS:
        if target["family"] != "Chimera":
            assert target["execution"] in {"translated", "emulated", "imported"}
