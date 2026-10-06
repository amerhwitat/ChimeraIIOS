#!/usr/bin/env python3
import base64,gzip,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
src=ROOT/"data/isa/isa-registry.json.gz.b64"
out=ROOT/"kernel/generated/chimera_isa_registry.generated.h"
rows=json.loads(gzip.decompress(base64.b64decode(src.read_text().strip())))
out.parent.mkdir(parents=True,exist_ok=True)
def esc(s): return s.replace("\\","\\\\").replace('"','\\"')
lines=["#pragma once","#include <stdint.h>","struct chimera_isa_entry { const char* family; const char* architecture; const char* mnemonic; const char* opcode; const char* encoding; const char* operands; const char* description; uint16_t bits; };","static const chimera_isa_entry CHIMERA_ISA_REGISTRY[] = {"]
for r in rows:
    lines.append('  {"%s","%s","%s","%s","%s","%s","%s",%s},'%(esc(r["Family"]),esc(r["Architecture"]),esc(r["Mnemonic"]),esc(r["OpcodeHex"]),esc(r["Encoding"]),esc(r["Operands"]),esc(r["Description"]),r["Bits"] or 0))
lines.append("};")
lines.append("static const uint32_t CHIMERA_ISA_REGISTRY_COUNT = sizeof(CHIMERA_ISA_REGISTRY)/sizeof(CHIMERA_ISA_REGISTRY[0]);")
out.write_text("\n".join(lines)+"\n",encoding="utf-8")
print(f"generated {len(rows)} ISA entries -> {out}")
