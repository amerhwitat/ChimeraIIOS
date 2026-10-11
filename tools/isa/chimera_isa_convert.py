#!/usr/bin/env python3
"""Fail-closed ISA inventory and semantic-IR conversion planner.

This emits CHIR semantic-IR plans only; it does not decode arbitrary binaries,
assemble machine code, or claim CPU/ISA conformance.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DB_PATH=ROOT/"isa"/"isa_database.json"
OPS={"add","sub","and","or","xor","shift-left","shift-right-logical","shift-right-arithmetic","move","load-immediate","nop","multiply","set-less-than-signed","set-less-than-unsigned"}
def load_db():
    data=json.loads(DB_PATH.read_text(encoding="utf-8"))
    if not isinstance(data.get("architectures"),list) or not isinstance(data.get("execution_model",{}).get("translation_profiles"),list):
        raise ValueError("canonical ISA database lacks translation profiles")
    return data
def plan(db,architecture,mnemonic,mode):
    if not any(a[0]==architecture for a in db["architectures"]): raise ValueError(f"unknown architecture: {architecture}")
    profiles=db["execution_model"]["translation_profiles"]
    profile=next((p for p in profiles if p["architecture"]==architecture),None)
    if profile is None: raise ValueError(f"no conversion profile for architecture: {architecture}")
    candidates=[c for c in db["execution_model"].get("execution_candidates",[]) if c.get("architecture")==architecture and c.get("kind")=="instruction-candidate" and c.get("mnemonic","").upper()==mnemonic.upper()]
    if not candidates: raise ValueError(f"no catalogued instruction form for {architecture}:{mnemonic}")
    mapped=[c for c in candidates if c.get("semantic_operation") in OPS]
    if not mapped: raise ValueError(f"{architecture}:{mnemonic} has no approved semantic-operation mapping")
    if mode=="compatibility" and profile["compatibility_mode"]["status"]!="reference-subset-only":
        raise ValueError(f"compatibility backend unavailable for {architecture}; refusing to guess")
    if mode=="compatibility" and architecture!="riscv32":
        raise ValueError("only the RV32I reference subset is currently wired to a decoder")
    c=mapped[0]; op=c["semantic_operation"]
    return {"schema":"CHIR-PLAN-1","source":{"architecture":architecture,"mnemonic":mnemonic.upper(),"candidate_id":c["id"],"source_ref":c.get("source_ref"),"candidate_status":c.get("candidate_status")},"mode":mode,"target":{"ir_opcode":"CHIR."+op.upper().replace("-","_"),"semantic_operation":op},"status":"semantic-ir-plan-only","machine_code_emitted":False,"execution_verified":False,"conformance_status":c.get("conformance_status","not-tested"),"note":"A plan only: operands, flags, memory ordering, traps, privilege and ABI semantics must be validated by a target backend."}
def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__); sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("inventory",help="show architecture conversion-profile coverage")
    p=sub.add_parser("plan",help="plan a catalogued instruction to CHIR semantic IR"); p.add_argument("architecture"); p.add_argument("mnemonic"); p.add_argument("--mode",choices=("native","compatibility"),default="native")
    args=parser.parse_args(argv)
    try:
        db=load_db()
        if args.command=="inventory":
            result={"schema":"CHIMERA-ISA-INVENTORY-1","architecture_count":len(db["architectures"]),"profile_count":len(db["execution_model"]["translation_profiles"]),"instruction_candidate_count":len(db["execution_model"].get("execution_candidates",[])),"profiles":db["execution_model"]["translation_profiles"]}
        else: result=plan(db,args.architecture,args.mnemonic,args.mode)
        print(json.dumps(result,ensure_ascii=False,indent=2)); return 0
    except (OSError,json.JSONDecodeError,ValueError) as exc:
        print(f"ISA conversion refused: {exc}",file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())
