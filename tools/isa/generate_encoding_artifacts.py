#!/usr/bin/env python3
"""Generate validated worked ISA encodings as JSON and a kernel lookup table."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "isa" / "catalog.json"
data = json.loads(CATALOG.read_text(encoding="utf-8"))
samples = []
for insn in data.get("instructions", []):
    enc = insn["encoding"]
    sample = enc["sample"]
    binary, hexa, bits = sample["binary"], sample["hex"], enc["length_bits"]
    if len(binary) != bits or set(binary) - {"0", "1"} or int(binary, 2) != int(hexa, 16):
        raise SystemExit(f"invalid exact sample encoding: {insn.get('id')}")
    sources = [s["url"] for s in data.get("sources", []) if insn["family"] in s.get("families", [])]
    samples.append({
        "id": insn["id"], "family": insn["family"], "mnemonic": insn["mnemonic"],
        "syntax": insn["syntax"], "bits": bits, "binary": binary, "hex": hexa,
        "fields": enc["fields"], "source_urls": sources
    })
out = ROOT / "isa" / "generated" / "isa-encoding-samples.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({
    "schema": "CHM-ISA-SAMPLES-1",
    "scope": "Worked sample encodings only; not an exhaustive ISA or a complete encoder/decoder.",
    "count": len(samples), "samples": samples
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def q(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

header = [
    "#pragma once", "#include <stdint.h>",
    "struct chimera_isa_sample_entry { const char* family; const char* mnemonic; const char* syntax; const char* binary; const char* hex; uint16_t bits; };",
    "static const chimera_isa_sample_entry CHIMERA_ISA_SAMPLES[] = {"
]
for item in samples:
    header.append('  {"%s","%s","%s","%s","%s",%d},' % (
        q(item["family"]), q(item["mnemonic"]), q(item["syntax"]),
        item["binary"], item["hex"], item["bits"]))
header += [
    "};",
    "static const uint32_t CHIMERA_ISA_SAMPLE_COUNT = sizeof(CHIMERA_ISA_SAMPLES)/sizeof(CHIMERA_ISA_SAMPLES[0]);",
    ""
]
(ROOT / "kernel" / "generated" / "chimera_isa_encoding_samples.generated.h").write_text(
    "\n".join(header), encoding="utf-8")
print(f"Generated {len(samples)} verified ISA sample encodings (binary + hex)")
