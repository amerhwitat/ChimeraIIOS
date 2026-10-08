#!/usr/bin/env python3
"""Generate checked ISA encoding templates and worked samples for kernel lookup."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = json.loads((ROOT / "isa" / "catalog.json").read_text(encoding="utf-8"))
DB = json.loads((ROOT / "isa" / "isa_database.json").read_text(encoding="utf-8"))
families = {row[0]: row[2] for row in DB.get("architectures", []) if len(row) >= 3}
templates = []
for row in DB.get("instructions", []):
    arch, mnemonic, form, operands, syntax, bits, value, mask = row
    bits = int(bits)
    binary, mask_binary = str(value), str(mask)
    if len(binary) != bits or len(mask_binary) != bits or set(binary) - {"0", "1"} or set(mask_binary) - {"0", "1"}:
        raise SystemExit(f"invalid encoding template: {arch}/{mnemonic}")
    width = (bits + 3) // 4
    templates.append({
        "architecture": arch, "family": families.get(arch, arch), "mnemonic": mnemonic,
        "form": form, "operands": operands, "syntax": syntax, "bits": bits,
        "binary": binary, "hex": "0x" + format(int(binary, 2), f"0{width}X"),
        "mask_binary": mask_binary, "mask_hex": "0x" + format(int(mask_binary, 2), f"0{width}X"),
        "encoding_kind": "canonical-pattern-with-variable-fields"
    })
samples = []
for insn in CATALOG.get("instructions", []):
    enc, sample = insn["encoding"], insn["encoding"]["sample"]
    binary, hexa, bits = sample["binary"], sample["hex"], enc["length_bits"]
    if len(binary) != bits or set(binary) - {"0", "1"} or int(binary, 2) != int(hexa, 16):
        raise SystemExit(f"invalid exact sample encoding: {insn.get('id')}")
    sources = [s["url"] for s in CATALOG.get("sources", []) if insn["family"] in s.get("families", [])]
    samples.append({
        "id": insn["id"], "family": insn["family"], "mnemonic": insn["mnemonic"],
        "syntax": insn["syntax"], "bits": bits, "binary": binary, "hex": hexa,
        "fields": enc["fields"], "source_urls": sources
    })
json_path = ROOT / "isa" / "generated" / "isa-encoding-registry.json"
json_path.parent.mkdir(parents=True, exist_ok=True)
json_path.write_text(json.dumps({
    "schema": "CHM-ISA-ENCODING-REGISTRY-2",
    "scope": "Encoding templates are canonical bit patterns with masks; worked samples are exact operand examples. Neither list implies exhaustive ISA/backend support.",
    "template_count": len(templates), "sample_count": len(samples),
    "encoding_templates": templates, "worked_samples": samples
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
# Keep the earlier sample-only JSON as a stable lightweight view.
(ROOT / "isa" / "generated" / "isa-encoding-samples.json").write_text(json.dumps({
    "schema": "CHM-ISA-SAMPLES-1",
    "scope": "Worked sample encodings only; not an exhaustive ISA or a complete encoder/decoder.",
    "count": len(samples), "samples": samples
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def q(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
header = [
    "#pragma once", "#include <stdint.h>",
    "struct chimera_isa_template_entry { const char* architecture; const char* family; const char* mnemonic; const char* form; const char* syntax; const char* binary; const char* hex; const char* mask_binary; const char* mask_hex; uint16_t bits; };",
    "static const chimera_isa_template_entry CHIMERA_ISA_ENCODING_TEMPLATES[] = {"
]
for x in templates:
    header.append('  {"%s","%s","%s","%s","%s","%s","%s","%s","%s",%d},' % (
        q(x["architecture"]), q(x["family"]), q(x["mnemonic"]), q(x["form"]),
        q(x["syntax"]), x["binary"], x["hex"], x["mask_binary"], x["mask_hex"], x["bits"]))
header += [
    "};",
    "static const uint32_t CHIMERA_ISA_ENCODING_TEMPLATE_COUNT = sizeof(CHIMERA_ISA_ENCODING_TEMPLATES)/sizeof(CHIMERA_ISA_ENCODING_TEMPLATES[0]);",
    "struct chimera_isa_sample_entry { const char* family; const char* mnemonic; const char* syntax; const char* binary; const char* hex; uint16_t bits; };",
    "static const chimera_isa_sample_entry CHIMERA_ISA_SAMPLES[] = {"
]
for x in samples:
    header.append('  {"%s","%s","%s","%s","%s",%d},' % (
        q(x["family"]), q(x["mnemonic"]), q(x["syntax"]), x["binary"], x["hex"], x["bits"]))
header += [
    "};",
    "static const uint32_t CHIMERA_ISA_SAMPLE_COUNT = sizeof(CHIMERA_ISA_SAMPLES)/sizeof(CHIMERA_ISA_SAMPLES[0]);",
    ""
]
(ROOT / "kernel" / "generated" / "chimera_isa_encoding_samples.generated.h").write_text(
    "\n".join(header), encoding="utf-8")
print(f"Generated {len(templates)} ISA encoding templates and {len(samples)} worked samples")
