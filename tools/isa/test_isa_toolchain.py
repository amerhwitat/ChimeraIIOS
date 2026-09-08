#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys, tempfile
from pathlib import Path

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[2]); args=ap.parse_args(); root=args.root.resolve()
    generator=root/"tools/isa/generate_isa_bitfields.py"; checker=root/"tools/isa/test_isa_conformance.py"
    with tempfile.TemporaryDirectory(prefix="chimera-isa-") as td:
        out=Path(td)/"isa_bitfields.json"
        subprocess.run([sys.executable,str(generator),"--output",str(out)],cwd=root,check=True)
        subprocess.run([sys.executable,str(checker),str(out)],cwd=root,check=True)
        doc=json.loads(out.read_text(encoding="utf-8")); instructions=doc["instructions"]
        assert doc["canonical_abi"]["bytes"]==16
        assert len(instructions)==doc["instruction_count"]==284
        assert {int(x["opcode"],16) for x in instructions}==set(range(1,0x11D))
        assert any(x["mnemonic"]=="ADD" and x["opcode"]=="0x0001" for x in instructions)
        assert any(x["mnemonic"]=="PIPEWIRE_PUBLISH" and x["opcode"]=="0x0092" for x in instructions)
        assert any(x["mnemonic"]=="POLICY_AUDIT" and x["opcode"]=="0x011C" for x in instructions)
    print("PASS: generator + JSON schema + complete 284-opcode ISA conformance harness")
    return 0
if __name__=="__main__": raise SystemExit(main())
