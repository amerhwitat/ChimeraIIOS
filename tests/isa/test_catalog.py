import json
import re
from pathlib import Path

ROOT = Path(__file__).parents[2]
CATALOG = ROOT / "isa" / "catalog.json"


def load_catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def bits_to_int(bits: str) -> int:
    assert re.fullmatch(r"[01]+", bits)
    return int(bits, 2)


def test_catalog_has_major_risc_and_cisc_families():
    data = load_catalog()
    families = {x["id"] for x in data["families"]}
    assert {"riscv", "aarch64", "arm32", "mips32", "power", "sparc", "x86", "m68k", "systemz", "vax"} <= families


def test_every_instruction_has_operands_and_encoding_metadata():
    data = load_catalog()
    ids = set()
    family_ids = {f["id"] for f in data["families"]}
    for insn in data["instructions"]:
        assert insn["id"] not in ids
        ids.add(insn["id"])
        assert insn["family"] in family_ids
        assert insn["mnemonic"]
        assert isinstance(insn["operands"], list)
        length = insn["encoding"]["length_bits"]
        assert 8 <= length <= 128 and length % 8 == 0
        assert insn["encoding"]["fields"]
        sample = insn["encoding"]["sample"]
        bits_to_int(sample["binary"])
        assert len(sample["binary"]) == length
        assert sample["hex"].lower() == format(int(sample["binary"], 2), "#x")


def test_optional_operands_are_explicit():
    data = load_catalog()
    assert any(any(o.get("optional") for o in i["operands"]) for i in data["instructions"])


def test_sources_are_recorded():
    data = load_catalog()
    assert len(data["sources"]) >= 5
    for source in data["sources"]:
        assert source["url"].startswith("https://")
        assert source["scope"]


DATABASE = ROOT / "isa" / "isa_database.json"


def test_universal_database_instruction_candidates_have_effect_and_implementation_plans():
    data = json.loads(DATABASE.read_text(encoding="utf-8"))
    source_ids = {source["id"] for source in data["sources"]}
    candidates = [
        item for item in data["execution_model"]["execution_candidates"]
        if item.get("kind") == "instruction-candidate"
    ]
    assert candidates
    for item in candidates:
        assert item["source_ref"] in source_ids, item["id"]
        assert item["encoding_hex_template"].startswith("0x"), item["id"]
        assert item["affected_registers_model"]["reads"]
        assert item["affected_registers_model"]["writes"]
        assert item["flags_effect_model"]["affected"]
        assert item["memory_effect_model"]["class"]
        plan = item["best_implementation"]
        assert plan["recommended_strategy"]
        assert plan["native_mode"] and plan["compatibility_mode"] and plan["n_bit_mode"]
        assert plan["validation_gate"]
        assert plan["status"] == "recommendation-only; implementation and conformance unverified"
        if "exact_example" in item:
            example = item["exact_example"]
            assert len(example["binary_bits"]) == example["length_bits"]
            assert int(example["hex_word"], 16) == int(example["binary_bits"], 2)


def test_worked_encoding_samples_have_consistent_binary_hex_and_register_effects():
    data = json.loads(DATABASE.read_text(encoding="utf-8"))
    source_ids = {source["id"] for source in data["sources"]}
    assert len(data["verified_encoding_samples"]) >= 20
    for sample in data["verified_encoding_samples"]:
        assert sample["source_ref"] in source_ids, sample
        bits = sample["binary_bits"]
        assert len(bits) == sample["length_bits"]
        assert re.fullmatch(r"[01]+", bits)
        assert int(sample["hex_word"], 16) == int(bits, 2)
        assert sample["affected_registers"]
        assert "status" in sample["chimera_nbit_mapping"]
