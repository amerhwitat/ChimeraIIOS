# Chimera II ISA Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand Chimera II OS's ISA registry into a validated, provenance-first instruction database with operands and binary encoding metadata for Chimera-native, RISC, and CISC families.

**Architecture:** Keep `world_architectures.json` as the family index; make `isa_database.json` canonical for normalized architecture/instruction records; export instruction records to `instructions.json` and SQLite-compatible `isa_database.sql`. A Python validator enforces cross-file references, encoding integrity, and duplicate-free instruction forms.

**Tech Stack:** JSON, SQLite SQL, Python 3 standard library, pytest.

**Spec:** `docs/superpowers/specs/2026-09-16-isa-registry-design.md`

## Global Constraints

- Do not claim an invented Chimera opcode is an industry-standard encoding.
- Store fixed opcode/value masks separately from operand fields.
- Store canonical concrete encodings only where operand values can be chosen deterministically.
- Preserve authoritative-source provenance for every architecture family.
- Never copy proprietary manuals wholesale; retain normalized metadata and short encoding descriptors.

---

### Task 1: Add regression tests for the ISA registry

**Files:**
- Create: `tests/test_isa_registry.py`

**Interfaces:**
- Consumes: `isa/isa_database.json`, `isa/instructions.json`, `isa/world_architectures.json`.
- Produces: deterministic validation tests that fail until the new registry exists.

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest -q tests/test_isa_registry.py`
Expected: FAIL because the new database files do not yet exist.

- [ ] **Step 3: Commit**

```bash
git add tests/test_isa_registry.py
git commit -m "test: define ISA registry invariants"
```

### Task 2: Build the normalized ISA database

**Files:**
- Create: `isa/isa_database.json`
- Create: `isa/instructions.json`
- Create: `isa/isa_database.sql`
- Modify: `isa/world_architectures.json`

**Interfaces:**
- Consumes: authoritative RISC-V, Arm, Intel/AMD, IBM, SPARC and project architecture references.
- Produces: normalized architecture records and at least 100 instruction forms with operand kinds, encoding fields, fixed opcode/value-mask bits, canonical binary examples where valid, semantics and provenance.

- [ ] **Step 1: Add architecture families and encoding models**
- [ ] **Step 2: Add instruction forms for integer, control-flow, load/store, system/atomic/vector/crypto operations where the source architecture supports them.**
- [ ] **Step 3: Add Chimera C8192/R8192 custom instruction namespace and mark it project-defined.**
- [ ] **Step 4: Export the instruction-focused view and SQLite schema/data.**
- [ ] **Step 5: Update `world_architectures.json` to reference the database and coverage metadata.**

### Task 3: Add machine validation tooling

**Files:**
- Create: `tools/validate_isa_registry.py`
- Create: `tools/isa_registry_report.py`

**Interfaces:**
- `validate_isa_registry.py` exits nonzero for malformed or inconsistent records.
- `isa_registry_report.py` prints architecture/instruction counts and coverage by RISC/CISC/custom class.

- [ ] **Step 1: Implement validation from the failing tests.**
- [ ] **Step 2: Add duplicate, bit-width, reference and provenance checks.**
- [ ] **Step 3: Add a concise human-readable coverage report.**
- [ ] **Step 4: Run both tools.**

### Task 4: Integrate documentation and source provenance

**Files:**
- Create: `isa/README.md`
- Modify: `README.md`

**Interfaces:**
- Documents registry semantics, binary-pattern conventions, supported families and authoritative source links.

- [ ] **Step 1: Document fixed opcode/value-mask versus operand fields.**
- [ ] **Step 2: Document current architecture coverage and known completeness boundaries.**
- [ ] **Step 3: Link the ISA registry from the root README.**

### Task 5: Final verification

- [ ] **Step 1: Run `python tools/validate_isa_registry.py`.**
- [ ] **Step 2: Run `python tools/isa_registry_report.py`.**
- [ ] **Step 3: Run `pytest -q tests/test_isa_registry.py`.**
- [ ] **Step 4: Parse every JSON file touched by the change.**
- [ ] **Step 5: Inspect the final git diff and commit history.**
