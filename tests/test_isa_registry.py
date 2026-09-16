import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_registry_has_required_architectures_and_instruction_forms():
    db = load("isa/isa_database.json")
    ids = {row["id"] for row in db["architectures"]}
    assert {"chimera-c8192", "chimera-r8192", "x86-64", "aarch64", "riscv64", "mips32"} <= ids
    assert len(db["instructions"]) >= 100


def test_instruction_records_have_operands_and_encoding():
    db = load("isa/isa_database.json")
    for row in db["instructions"]:
        assert row["mnemonic"]
        assert row["operands"]
        assert row["encoding"]["length_bits"] >= 8
        assert row["encoding"]["value_bits"]
        assert row["semantics"]["inputs"] is not None


def test_binary_fields_are_well_formed():
    db = load("isa/isa_database.json")
    for row in db["instructions"]:
        for key in ("value_bits", "mask_bits"):
            bits = row["encoding"][key]
            assert set(bits) <= {"0", "1"}
            assert len(bits) == row["encoding"]["length_bits"]


def test_instruction_forms_are_unique():
    db = load("isa/isa_database.json")
    keys = [(x["architecture"], x["mnemonic"], x["form_id"]) for x in db["instructions"]]
    assert len(keys) == len(set(keys))
