#!/usr/bin/env python3
"""Generate validated ISA encoding templates and exact worked samples.

The reference catalog is authoritative for worked samples. The legacy positional
database may contain recovered rows whose bit masks are explicitly unavailable;
those rows are not templates and must be skipped rather than treated as fatal or
silently converted into fabricated encodings.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "isa" / "catalog.json"
DB_PATH = ROOT / "isa" / "isa_database.json"
CATALOG = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
DB = json.loads(DB_PATH.read_text(encoding="utf-8"))

families = {
    row[0]: row[2]
    for row in DB.get("architectures", [])
    if isinstance(row, list) and len(row) >= 3
}
# Catalog family metadata takes precedence when the recovered DB lacks a family.
families.update({
    row["id"]: row.get("description", row["id"])
    for row in CATALOG.get("families", [])
    if isinstance(row, dict) and isinstance(row.get("id"), str)
})

templates = []
skipped_templates = []
for row in DB.get("instructions", []):
    if not isinstance(row, (list, tuple)) or len(row) != 8:
        skipped_templates.append("<malformed-row>")
        continue
    arch, mnemonic, form, operands, syntax, bits_raw, value, mask = row
    try:
        bits = int(bits_raw)
    except (TypeError, ValueError):
        skipped_templates.append(f"{arch}/{mnemonic}")
        continue
    binary, mask_binary = str(value), str(mask)
    # A recovered catalog can intentionally mark a mask unavailable. Never
    # mislabel such a row as an encoding template or stop exact-sample output.
    valid_width = bits > 0 and bits <= 65535
    valid_binary = bool(re.fullmatch(r"[01]+", binary)) and len(binary) == bits
    valid_mask = bool(re.fullmatch(r"[01]+", mask_binary)) and len(mask_binary) == bits
    if not (valid_width and valid_binary and valid_mask):
        skipped_templates.append(f"{arch}/{mnemonic}")
        continue
    width = (bits + 3) // 4
    templates.append({
        "architecture": arch, "family": families.get(arch, arch),
        "mnemonic": mnemonic, "form": form, "operands": operands,
        "syntax": syntax, "bits": bits, "binary": binary,
        "hex": "0x" + format(int(binary, 2), f"0{width}X"),
        "mask_binary": mask_binary,
        "mask_hex": "0x" + format(int(mask_binary, 2), f"0{width}X"),
        "encoding_kind": "canonical-pattern-with-variable-fields"
    })

samples = []
for insn in CATALOG.get("instructions", []):
    try:
        enc = insn["encoding"]
        sample = enc["sample"]
        bits = int(enc["length_bits"])
        binary, hexa = sample["binary"], sample["hex"]
    except (KeyError, TypeError, ValueError) as exc:
        raise SystemExit(f"invalid exact sample structure: {insn.get('id', '<unknown>')}: {exc}")
    if (bits <= 0 or len(binary) != bits or not re.fullmatch(r"[01]+", binary)
            or not re.fullmatch(r"0[xX][0-9a-fA-F]+", hexa)
            or int(binary, 2) != int(hexa, 16)):
        raise SystemExit(f"invalid exact sample encoding: {insn.get('id')}")
    sources = [
        source["url"] for source in CATALOG.get("sources", [])
        if insn["family"] in source.get("families", []) and source.get("url")
    ]
    samples.append({
        "id": insn["id"], "family": insn["family"],
        "mnemonic": insn["mnemonic"], "syntax": insn["syntax"],
        "bits": bits, "binary": binary, "hex": hexa,
        "fields": enc["fields"], "source_urls": sources
    })

generated = ROOT / "isa" / "generated"
generated.mkdir(parents=True, exist_ok=True)
(generated / "isa-encoding-registry.json").write_text(json.dumps({
    "schema": "CHM-ISA-ENCODING-REGISTRY-2",
    "scope": "Only rows with verified-width binary patterns and masks are templates. Worked samples are exact operand examples. Neither list implies exhaustive ISA/backend support.",
    "template_count": len(templates), "sample_count": len(samples),
    "skipped_template_count": len(skipped_templates),
    "skipped_templates": skipped_templates,
    "encoding_templates": templates, "worked_samples": samples
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
# Keep the sample-only JSON as a stable lightweight view.
(generated / "isa-encoding-samples.json").write_text(json.dumps({
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

print(f"Generated {len(templates)} verified ISA encoding templates and {len(samples)} exact worked samples")
if skipped_templates:
    print(f"Warning: skipped {len(skipped_templates)} database rows with missing/invalid template masks; exact catalog samples were still generated.")
