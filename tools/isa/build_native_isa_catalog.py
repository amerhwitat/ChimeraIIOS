#!/usr/bin/env python3
"""Normalize every discovered ISA inventory entry into Chimera native views.

Nothing here relabels metadata as implementation. The sourced universal catalog
is read but never rewritten: its official conformance_tested=0 and
not_implemented=1613 counts remain authoritative. This generator emits a SEPARATE
derived catalogue with explicit per-row backend status and architecture-owned
semantics (CISC x86-64, RISC aarch64, RISC riscv64, and every other family).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "isa"))
from chimera_native_isa import (  # noqa: E402
    BACKENDS, CATALOG_VECTORS, MASK64, assemble, disassemble,
    arch_identity, effects,
)

SCHEMA = "CHM-ISA-NATIVE-1"
DEFAULT_OUT = ROOT / "isa" / "generated" / "chimera-native-isa-catalog.json"
FORMATS_OUT = ROOT / "tools" / "chimera-asm" / "chimera_native_formats.json"
UNIVERSAL_PATH = ROOT / "isa" / "generated" / "universal-instruction-catalog.json"

INPUTS: list[tuple[str, str, str]] = [
    ("isa/isa_database.json", "inventory", "104 architecture rows and 154 legacy instruction forms"),
    (UNIVERSAL_PATH.relative_to(ROOT).as_posix(), "official-catalog", "1613 sourced instruction records; read-only"),
    ("system/commands/command-isa-coverage.json", "inventory", "104 architecture inventory entries; command-side counts"),
    ("isa/catalog.json", "research", "54 researched instruction samples with field descriptions"),
    ("isa/generated/isa-encoding-registry.json", "research", "154 encoding templates and 54 worked samples"),
    ("isa/generated/isa-encoding-samples.json", "research", "54 encoding samples"),
    ("tools/chimera-asm/chimera_isa.json", "chimera-native", "authoritative CHM-ISA-1 16-byte uop definition"),
    ("tools/isa/isa_opcodes.csv", "chimera-native", "R8192 opcode inventory"),
    ("tools/isa/isa_opcodes_expanded_with_encodings.csv", "chimera-native", "expanded R8192 encoding templates"),
    ("tools/isa/chimera_r8192_opcode_index.csv", "chimera-native", "R8192 opcode index"),
    ("tools/isa/local_isa_catalog.json", "local-profiles", "28 local n-bit profiles"),
    ("data/isa/online-isa-index.json", "research", "online candidate index; not implementation evidence"),
    ("docs/research/isa-command-research.json", "research", "273 local files, 15 official docs, 8 GitHub searches"),
    ("system/commands/command-runtime-capabilities.json", "command-side", "4144 command capability records"),
    ("system/commands/native-command-candidates.json", "command-side", "4084 command candidates, 15 allowlisted"),
    (".github/workflows/command-isa-matrix.yml", "command-side", "native command cross-build workflow; no ISA implementation claim"),
]


def load_json(rel: str) -> Any:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def csv_count(rel: str) -> int:
    with (ROOT / rel).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    return max(0, len(rows) - 1)


def input_manifest() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    for rel, role, note in INPUTS:
        path = ROOT / rel
        entry: dict[str, Any] = {"path": rel, "role": role, "note": note,
                                 "present": path.exists(), "records": None}
        if path.exists():
            if path.suffix == ".json":
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    for key in ("instructions", "records", "commands", "architectures", "instruction_families",
                                "encoding_templates", "worked_samples", "sources", "profiles", "local_files",
                                "official_documentation", "github_searches"):
                        if isinstance(data.get(key), list):
                            entry.setdefault("counts", {})[key] = len(data[key])
                    if "record_count" in data:
                        entry.setdefault("counts", {})["record_count"] = data["record_count"]
                elif isinstance(data, list):
                    entry["records"] = len(data)
            elif path.suffix == ".csv":
                entry["records"] = csv_count(rel)
            else:
                entry["records"] = len(path.read_text(encoding="utf-8").splitlines())
        manifest.append(entry)
    by_path = {e["path"]: e for e in manifest}
    return manifest, by_path


def operand_view(row: dict[str, Any], decoded: Any | None, word_bits: int) -> dict[str, Any]:
    """Describe operands without inventing source-missing semantics."""
    if decoded is not None:
        specs: list[dict[str, Any]] = []
        for key in ("dst", "src", "reg", "rel", "rd", "rn", "rm", "rt", "rs1", "rs2", "off", "imm", "pred", "succ"):
            if key not in decoded.operands:
                continue
            value = decoded.operands[key]
            if isinstance(value, dict) and value.get("kind") == "mem":
                specs.append({"role": key, "type": "memory", "width_bits": word_bits,
                              "addressing_mode": "base+index*scale+displacement" if value.get("index") is not None
                              else "base+displacement" if value.get("base") is not None else "absolute-displacement"})
            elif isinstance(value, dict) and value.get("kind") == "reg":
                specs.append({"role": key, "type": "register", "width_bits": word_bits, "addressing_mode": "register-direct"})
            elif key == "rel":
                specs.append({"role": key, "type": "pc-relative-offset", "width_bits": 32, "addressing_mode": "pc-relative"})
            elif key in ("off", "imm", "pred", "succ"):
                specs.append({"role": key, "type": "immediate", "width_bits": "form-defined",
                              "addressing_mode": "immediate"})
            else:
                specs.append({"role": key, "type": "register", "width_bits": word_bits, "addressing_mode": "register-direct"})
        if specs:
            return {"count": len(specs), "items": specs, "provenance": "real-backend-decoded"}
    raw = row.get("operands", [])
    if isinstance(raw, str):
        types = ["unspecified-source-fields"]
    elif isinstance(raw, list):
        types = [str(x) for x in raw] or ["implicit"]
    else:
        types = ["unknown"]
    widths = []
    for kind in types:
        lowered = kind.lower()
        if "register" in lowered:
            widths.append(word_bits)
        elif "memory" in lowered:
            widths.append(word_bits)
        elif "immediate" in lowered:
            widths.append("source-unspecified")
        elif "branch" in lowered or "offset" in lowered:
            widths.append("source-unspecified")
        elif "implicit" in lowered:
            widths.append(0)
        else:
            widths.append("source-unspecified")
    syntax = str(row.get("syntax", ""))
    if "[" in syntax or "(" in syntax:
        modes = ["base+displacement"]
    elif "rel" in syntax or any(t.lower() == "branch-offset" for t in types):
        modes = ["pc-relative"]
    elif "implicit" in syntax.lower() or types == ["implicit"]:
        modes = ["implicit"]
    else:
        modes = ["register-direct-or-source-defined"]
    return {"count": len(types), "types": types, "widths_bits": widths,
            "addressing_modes": modes, "provenance": "source-metadata-only"}


def native_format(row: dict[str, Any], arch_meta: dict[str, Any], backend: Any | None,
                  decoded: Any | None, form_key: tuple[str, str] | None) -> dict[str, Any]:
    value_bits, mask_bits = row.get("value_bits"), row.get("mask_bits")
    base: dict[str, Any] = {
        "semantics_owner": row["architecture"],
        "native_family": arch_meta["native_family"],
        "format_class": arch_meta["encoding_model"],
        "fixed_value_bits": value_bits,
        "fixed_mask_bits": mask_bits,
        "opcode": row.get("opcode_hex"),
        "endianness": row.get("instruction_byte_order", row.get("endianness")),
        "descriptor_only": True,
        "note": "Sourced fixed-bit descriptor only; no real encoder/decoder/executor is claimed.",
    }
    if backend is not None and decoded is not None and form_key is not None:
        spec = backend.formats()[form_key]
        order = "big" if row["architecture"] == "x86-64" else "little"
        word = int.from_bytes(decoded.data, order)
        base.update({
            "descriptor_only": False,
            "format_class": spec["format_class"],
            "opcode": spec["opcode"],
            "bit_fields": spec["bit_fields"],
            "prefixes": spec.get("prefixes", []),
            "modrm_or_fixed_fields": {
                "kind": "ModRM/SIB" if row["architecture"] == "x86-64" else "fixed-field",
                "fixed_bits_match_sourced_mask": (word & int(mask_bits or "0", 2)) == (int(value_bits or "0", 2) & int(mask_bits or "0", 2)),
                "encoded_bytes": decoded.data.hex(),
            },
            "note": "Architecture-owned semantics; bytes stay in the source ISA's native format.",
        })
    return base


def effects_view(row: dict[str, Any], decoded: Any | None, arch: str) -> dict[str, Any]:
    if decoded is not None:
        return effects(arch, decoded)
    return {
        "registers_read": [], "registers_written": [], "registers_clobbered": [],
        "flags_read": list(row.get("flags_read") or []),
        "flags_written": list(row.get("flags_written") or []),
        "memory_effects": row.get("memory_effects", "unknown"),
        "privilege": row.get("privilege", "source-defined/unknown"),
        "provenance": "source-metadata-only; no register-effect inference from mnemonics",
    }


def normalize_instruction(row: dict[str, Any], arch_meta: dict[str, Any],
                          backend: Any | None) -> dict[str, Any]:
    arch, mnemonic, form = row["architecture"], row["mnemonic"], row["form_id"]
    key = (arch, mnemonic, form)
    vector = CATALOG_VECTORS.get(key)
    decoded = None
    roundtrip_ok = False
    if vector and backend is not None:
        decoded = assemble(arch, vector)
        back = disassemble(arch, decoded.data)
        roundtrip_ok = back.text == decoded.text
        mask = int(row["mask_bits"], 2)
        value = int(row["value_bits"], 2)
        order = "big" if arch == "x86-64" else "little"
        word = int.from_bytes(decoded.data, order)
        if not roundtrip_ok or (word & mask) != (value & mask):
            raise SystemExit(f"real backend disagrees with sourced mask for {key}: {decoded.data.hex()}")
    implemented = bool(decoded and roundtrip_ok)
    if arch not in BACKENDS:
        reason = f"no real encoder/decoder/execution backend exists for {arch}; sourced mask only"
    elif not implemented:
        reason = "form is outside the implemented vertical slice; descriptor only"
    else:
        reason = "real architecture-specific encoder/decoder with round-trip vector; execution covered by conformance runner"
    crc, _ = arch_identity(arch)
    return {
        "id": f"{arch}:{mnemonic}:{form}:{row['length_bits']}",
        "architecture": arch,
        "architecture_family": arch_meta["native_family"],
        "isa_class": arch_meta["class"],
        "mnemonic": mnemonic,
        "instruction_form": form,
        "syntax": row.get("syntax", ""),
        "description": row.get("description", ""),
        "native_format": native_format(row, arch_meta, backend, decoded, (mnemonic, form) if decoded else None),
        "operands": operand_view(row, decoded, arch_meta["word_bits"]),
        "options_prefixes_immediates": {
            "prefixes": next(iter(
                [backend.formats()[(mnemonic, form)].get("prefixes", [])] if implemented else [[]])),
            "options": backend.formats()[(mnemonic, form)].get("options", []) if implemented else [],
            "immediates": [item for item in (operand_view(row, decoded, arch_meta["word_bits"]).get("items", []))
                           if item.get("type") == "immediate"] if implemented else list(row.get("immediate_fields") or []),
        },
        "implementation": {
            "status": "real_backend" if implemented else "not_implemented",
            "backend": f"tools/isa/chimera_native_isa.py:{arch}" if implemented else None,
            "reason": reason,
            "native_object_arch_id": crc if implemented else None,
        },
        "effects": effects_view(row, decoded, arch),
        "effects_on_flags": {
            "read": list((effects_view(row, decoded, arch)).get("flags_read") or []),
            "written": list((effects_view(row, decoded, arch)).get("flags_written") or []),
            "provenance": "real-backend-model" if implemented else "source-metadata-only",
        },
        "memory_effects": effects_view(row, decoded, arch).get("memory_effects"),
        "privilege_level": effects_view(row, decoded, arch).get("privilege"),
        "conformance": {
            "official_status": "not-conformance-tested",
            "engineering_status": "roundtrip-vector-passed" if implemented else "descriptors-only",
            "official_conformance_tested": 0,
            "note": "Engineering round-trip evidence is not official conformance and never changes universal catalog counts.",
        },
        "semantics": {
            "owner": arch_meta["native_family"],
            "semantic_id": row.get("semantic_id"),
            "chimera_native_mapping": {
                "mode": "architecture-native-bytes-in-versioned-object",
                "encoder": f"chimera_native_isa.assemble({arch})" if implemented else None,
                "decoder": f"chimera_native_isa.disassemble({arch})" if implemented else None,
                "semantics": "source-architecture semantics preserved; no flattened Chimera opcode",
            } if implemented else None,
        },
        "source": {
            "ref": row.get("source_ref"), "revision": row.get("source_revision"),
            "sha256": row.get("source_sha256"), "license": row.get("license"),
            "encoding_status": row.get("encoding_status"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--formats-output", type=Path, default=FORMATS_OUT)
    parser.add_argument("--check", action="store_true", help="verify committed outputs match generated data")
    args = parser.parse_args()

    manifest, by_path = input_manifest()
    db = load_json("isa/isa_database.json")
    universal = load_json(UNIVERSAL_PATH.relative_to(ROOT).as_posix())
    coverage = load_json("system/commands/command-isa-coverage.json")
    chimera_isa = load_json("tools/chimera-asm/chimera_isa.json")

    arch_by_id = {a[0]: {"id": a[0], "class": a[1], "family": a[2], "word_bits": a[3],
                         "status": a[4], "encoding_model": a[5], "source_ref": a[6],
                         "instruction_forms": a[7]} for a in db["architectures"]}
    cov_by_id = {a["id"]: a for a in coverage["architectures"]}
    if set(arch_by_id) != set(cov_by_id):
        raise SystemExit("architecture inventory disagrees between isa_database.json and command-isa-coverage.json")
    row_counts: dict[str, int] = {}
    for row in universal["instructions"]:
        row_counts[row["architecture"]] = row_counts.get(row["architecture"], 0) + 1

    known_families = {"x86-64": "CISC x86-64", "aarch64": "RISC aarch64",
                      "riscv64": "RISC riscv64", "riscv32/riscv64": "RISC riscv (32/64 shared source)"}
    architectures = []
    for arch_id in sorted(arch_by_id):
        meta = arch_by_id[arch_id]
        backend = BACKENDS.get(arch_id)
        native_family = known_families.get(arch_id, f"{meta['class']} {meta['family']}")
        architectures.append({
            "id": arch_id, "family": meta["family"], "isa_class": meta["class"],
            "native_family": native_family, "word_bits": meta["word_bits"],
            "inventory_status": meta["status"], "encoding_model": meta["encoding_model"],
            "inventory_instruction_forms": meta["instruction_forms"],
            "universal_instruction_rows": row_counts.get(arch_id, 0),
            "real_backend": bool(backend),
            "status": "real_backend_slice" if backend else "descriptors_only_not_implemented",
            "reason": ("encoder/decoder/executor implemented at tools/isa/chimera_native_isa.py" if backend
                       else "inventory entry only: no real backend, executor, or conformance evidence"),
            "semantics_owner": native_family,
            "semantics_preserved": True,
            "native_object_arch_id": arch_identity(arch_id)[0],
            "command_inventory_binary_status": cov_by_id[arch_id].get("binary_status"),
        })

    arch_meta_by_id = {a["id"]: {"class": a["isa_class"], "family": a["family"],
                                 "native_family": a["native_family"], "word_bits": a["word_bits"],
                                 "encoding_model": a["encoding_model"]} for a in architectures}
    instructions = [normalize_instruction(row, arch_meta_by_id.get(row["architecture"], {
        "class": "unknown", "family": "unknown", "native_family": row["architecture"],
        "word_bits": row.get("length_bits", 32), "encoding_model": row.get("encoding", "unspecified")}),
        BACKENDS.get(row["architecture"])) for row in universal["instructions"]]
    implemented_count = sum(i["implementation"]["status"] == "real_backend" for i in instructions)
    formats = sorted({(a["architecture"], a["native_format"]["format_class"]) for a in instructions})
    native_formats = [
        {"architecture": arch, "format_class": fmt,
         "semantics_owner": arch_meta_by_id.get(arch, {}).get("native_family", arch),
         "descriptor_only": all(i["native_format"]["descriptor_only"] for i in instructions
                                if i["architecture"] == arch and i["native_format"]["format_class"] == fmt)}
        for arch, fmt in formats
    ]
    report = {
        "schema": SCHEMA,
        "generated_by": "tools/isa/build_native_isa_catalog.py",
        "policy": (
            "Architecture-owned instruction semantics are preserved. A sourced fixed-bit mask is a descriptor, "
            "not a backend. Only forms with real round-trip vectors are marked real_backend; all other rows "
            "are explicitly not_implemented with a reason. Official conformance counts are copied unchanged "
            "from the universal catalog and never upgraded by this derived report."
        ),
        "official_catalog": {
            "path": "isa/generated/universal-instruction-catalog.json",
            "schema": universal["schema"], "database_version": universal["database_version"],
            "record_count": universal["record_count"], "coverage": universal["coverage"],
        },
        "inventory": {
            "architecture_inventory_count": len(architectures),
            "instruction_record_count": len(instructions),
            "real_backend_instruction_rows": implemented_count,
            "descriptors_only_or_not_implemented_instruction_rows": len(instructions) - implemented_count,
            "real_backend_architectures": sorted(BACKENDS),
            "chimera_native_definition": {
                "path": "tools/chimera-asm/chimera_isa.json", "format": chimera_isa["format"],
                "machine": chimera_isa["machine"], "canonical_uop_bytes": chimera_isa["canonical_uop_bytes"],
                "instruction_families": chimera_isa["instruction_families"],
                "header": chimera_isa["binary_header"], "host_backends": chimera_isa["host_backends"],
            },
            "command_inventory": {
                "path": "system/commands/command-isa-coverage.json",
                "counts": coverage["counts"],
                "note": "Command-provider side is a separate workstream; instruction rows here are not command implementations.",
            },
            "research_evidence_only": {
                "path": "docs/research/isa-command-research.json",
                "counts": {k: by_path["docs/research/isa-command-research.json"]["counts"][k]
                           for k in ("local_files", "official_documentation", "github_searches")},
            },
            "inputs": manifest,
        },
        "native_formats": native_formats,
        "architectures": architectures,
        "instructions": instructions,
        "engineering_evidence": {
            "real_backend_form_vectors": len(CATALOG_VECTORS),
            "roundtrip_verified_rows": implemented_count,
            "execution_verified_rows": 0,
            "official_conformance_tested": universal["coverage"]["conformance_tested"],
            "official_not_implemented": universal["coverage"]["not_implemented"],
            "note": "Execution counts come from tools/isa/run_native_isa_conformance.py; this generator does not execute instructions.",
        },
    }
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    format_descriptors = {
        "schema": "CHM-ISA-NATIVE-FORMATS-1",
        "generated_by": "tools/isa/build_native_isa_catalog.py",
        "extends": {
            "path": "tools/chimera-asm/chimera_isa.json",
            "format": chimera_isa["format"], "machine": chimera_isa["machine"],
            "version": chimera_isa["version"], "register_model": chimera_isa["register_model"],
            "canonical_uop_bytes": chimera_isa["canonical_uop_bytes"],
            "note": ("Extends the CHM-ISA-1 canonical uop definition with architecture-native instruction "
                     "encodings. Source ISA bytes remain source-ISA bytes; no flattened Chimera opcode is invented."),
        },
        "object_format": {
            "magic": "CHMOBJ1", "version": 1, "abi_version": 1, "header_bytes": 64,
            "digest": "sha256-over-body", "footer_bytes": 32,
            "sections": ["NULL", "PROGBITS", "NOBITS", "STRTAB", "SYMTAB", "RELATAB", "NOTE"],
            "permissions": ["R", "W", "X"], "relocations": ["ABS64", "ABS32", "REL32"],
            "implementation": "tools/isa/chimera_native_isa.py",
        },
        "backends": {
            arch: {
                "family": backend.family, "endian": backend.endian,
                "formats": [
                    {"mnemonic": mnemonic, "form": form, **spec}
                    for (mnemonic, form), spec in sorted(backend.formats().items())
                ],
            }
            for arch, backend in sorted(BACKENDS.items())
        },
        "inventory_architectures": [
            {"id": a["id"], "isa_class": a["isa_class"], "native_family": a["native_family"],
             "word_bits": a["word_bits"], "real_backend": a["real_backend"], "status": a["status"]}
            for a in architectures
        ],
        "policy": report["policy"],
    }
    formats_payload = json.dumps(format_descriptors, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        for path, expected in ((args.output, payload), (args.formats_output, formats_payload)):
            if not path.exists():
                raise SystemExit(f"missing generated file: {path}")
            if path.read_text(encoding="utf-8") != expected:
                raise SystemExit(f"generated file is stale: {path}; run tools/isa/build_native_isa_catalog.py")
        print(f"native ISA outputs are current: {len(instructions)} rows, {len(BACKENDS)} real backends")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.formats_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
    args.formats_output.write_text(formats_payload, encoding="utf-8")
    print(f"wrote {args.output}: {len(architectures)} architectures, {len(instructions)} instruction rows, "
          f"{implemented_count} real_backend rows")
    print(f"wrote {args.formats_output}: {len(BACKENDS)} real backends, {len(architectures)} inventory entries")
    print(json.dumps({k: report["inventory"][k] for k in (
        "architecture_inventory_count", "instruction_record_count", "real_backend_instruction_rows",
        "descriptors_only_or_not_implemented_instruction_rows")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
