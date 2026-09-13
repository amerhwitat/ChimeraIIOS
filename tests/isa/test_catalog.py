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
    for insn in data["instructions"]:
        assert insn["id"] not in ids
        ids.add(insn["id"])
        assert insn["family"] in {f["id"] for f in data["families"]}
        assert insn["mnemonic"]
        assert isinstance(insn["operands"], list)
        assert insn["encoding"]["length_bits"] in (16, 32, 64)
        assert insn["encoding"]["fields"]
        sample = insn["encoding"]["sample"]
        bits_to_int(sample["binary"])
        assert len(sample["binary"]) == insn["encoding"]["length_bits"]
        assert sample["hex"].lower() == format(int(sample["binary"], 2), "0x")


def test_optional_operands_are_explicit():
    data = load_catalog()
    assert any(any(o.get("optional") for o in i["operands"]) for i in data["instructions"])


def test_sources_are_recorded():
    data = load_catalog()
    assert len(data["sources"]) >= 5
    for source in data["sources"]:
        assert source["url"].startswith("https://")
        assert source["scope"]
