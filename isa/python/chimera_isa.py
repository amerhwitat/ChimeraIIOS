"""Chimera II ISA catalog access. Canonical instruction data is isa/catalog.json."""
from dataclasses import dataclass
from pathlib import Path
import json

CATALOG = Path(__file__).resolve().parents[1] / "catalog.json"

@dataclass(frozen=True)
class Instruction:
    id: str
    family: str
    mnemonic: str
    syntax: str
    hex: str
    binary: str
    operands: tuple

def load_catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))

def instructions():
    return tuple(Instruction(i["id"], i["family"], i["mnemonic"], i["syntax"], i["encoding"]["sample"]["hex"], i["encoding"]["sample"]["binary"], tuple(i["operands"])) for i in load_catalog()["instructions"])
