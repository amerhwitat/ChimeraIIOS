import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_registry_has_required_architectures_and_instruction_forms():
    db = load("isa/isa_database.json")
    ids = {row[0] for row in db["architectures"]}
    assert {"chimera-c8192", "chimera-r8192", "x86-64", "aarch64", "riscv64", "mips32"} <= ids
    assert len(db["instructions"]) >= 100


def test_instruction_rows_have_operands_and_encoding():
    db = load("isa/isa_database.json")
    for row in db["instructions"]:
        architecture, mnemonic, form_id, operands, syntax, length_bits, value_bits, mask_bits = row
        assert architecture
        assert mnemonic
        assert form_id
        assert operands
        assert syntax
        assert length_bits >= 8
        assert len(value_bits) == length_bits
        assert len(mask_bits) == length_bits


def test_binary_fields_are_well_formed():
    db = load("isa/isa_database.json")
    for row in db["instructions"]:
        value_bits, mask_bits = row[6], row[7]
        assert set(value_bits) <= {"0", "1"}
        assert set(mask_bits) <= {"0", "1"}


def test_instruction_forms_are_unique():
    db = load("isa/isa_database.json")
    keys = [(x[0], x[1], x[2]) for x in db["instructions"]]
    assert len(keys) == len(set(keys))
