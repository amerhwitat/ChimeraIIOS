#!/usr/bin/env python3
"""Chimera ISA candidate catalog, mapping, and safe reference interpreter.

This is an instruction-level research harness, not a complete CPU emulator.
Only explicitly implemented semantic families execute; unsupported operations fail closed.
"""
from __future__ import annotations
import argparse
import json
import operator
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "isa" / "isa_database.json"

# Architecture-independent reference semantics. These are deliberately small,
# deterministic operations; they do not model privileged state or device effects.
OPS = {
    "ADD": ("add", lambda a,b,w: a+b), "ADDI": ("add", lambda a,b,w: a+b),
    "SUB": ("sub", lambda a,b,w: a-b), "SUBI": ("sub", lambda a,b,w: a-b),
    "AND": ("and", lambda a,b,w: a&b), "ANDI": ("and", lambda a,b,w: a&b),
    "OR": ("or", lambda a,b,w: a|b), "ORI": ("or", lambda a,b,w: a|b),
    "ORR": ("or", lambda a,b,w: a|b), "XOR": ("xor", lambda a,b,w: a^b),
    "EOR": ("xor", lambda a,b,w: a^b), "XORI": ("xor", lambda a,b,w: a^b),
    "SLL": ("shift-left", lambda a,b,w: a << (b % w)),
    "SLLI": ("shift-left", lambda a,b,w: a << (b % w)),
    "LSL": ("shift-left", lambda a,b,w: a << (b % w)),
    "SRL": ("shift-right-logical", lambda a,b,w: (a % (1<<w)) >> (b % w)),
    "SRLI": ("shift-right-logical", lambda a,b,w: (a % (1<<w)) >> (b % w)),
    "LSR": ("shift-right-logical", lambda a,b,w: (a % (1<<w)) >> (b % w)),
    "SRA": ("shift-right-arithmetic", lambda a,b,w: a >> (b % w)),
    "SRAI": ("shift-right-arithmetic", lambda a,b,w: a >> (b % w)),
    "MOV": ("move", lambda a,b,w: a), "MV": ("move", lambda a,b,w: a),
    "LI": ("load-immediate", lambda a,b,w: a),
    "NOP": ("nop", lambda a,b,w: a), "HINT": ("nop", lambda a,b,w: a),
    "MUL": ("multiply", lambda a,b,w: a*b),
    "SLT": ("set-less-than-signed", lambda a,b,w: int(a < b)),
    "SLTU": ("set-less-than-unsigned", lambda a,b,w: int((a%(1<<w)) < (b%(1<<w)))),
}
ARCH_BITS = {"chimera-c8192":8192, "chimera-r8192":8192, "x86-64":64, "x86-32":32,
 "aarch64":64, "arm32":32, "riscv32":32, "riscv64":64, "mips32":32, "mips64":64,
 "powerpc":32, "ppc64":64, "sparc-v9":64, "m68k":32, "s390x":64, "vax":32,
 "sh4":32, "loongarch64":64, "alpha":64, "hppa":64, "xtensa":32, "avr":8}
FORMATS = {
 "elf": {"description":"ELF object/executable; class and machine must match target","magic":"7f454c46","native_mode":"loader-required"},
 "pe-coff": {"description":"PE/COFF executable/object; machine field must match target","magic":"4d5a","native_mode":"loader-required"},
 "mach-o": {"description":"Mach-O executable/object; CPU type must match target","magic":"feedface/feedfacf/cefaedfe/cffaedfe","native_mode":"loader-required"},
 "raw": {"description":"Raw instruction bytes; no self-describing architecture or relocation metadata","magic":None,"native_mode":"requires-explicit-architecture"},
 "ncb": {"description":"Chimera Native Code Binary; project-defined container, validate its own header/version","magic":"project-defined","native_mode":"project-loader-required"},
 "wasm": {"description":"WebAssembly module; virtual ISA, not a general-purpose CPU ISA","magic":"0061736d","native_mode":"sandbox-runtime-required"},
}

def load_db():
    try: db=json.loads(DB_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: raise SystemExit(f"Cannot load ISA database {DB_PATH}: {exc}")
    if not isinstance(db.get("architectures"),list) or not isinstance(db.get("instructions"),list):
        raise SystemExit("ISA database missing architectures/instructions arrays")
    return db

def normalize(mnemonic):
    return str(mnemonic).strip().upper().split(".")[0]

def candidate_for_arch(arch, db):
    rows=[r for r in db["instructions"] if len(r)>=8 and r[0]==arch[0]]
    return rows

def build_candidates(db):
    candidates=[]
    for arch in db["architectures"]:
        if len(arch)<8: continue
        arch_id, kind, family, bits, status, encoding, source, count=arch[:8]
        forms=candidate_for_arch(arch,db)
        if not forms:
            candidates.append({"id":f"arch:{arch_id}","kind":"architecture-candidate","architecture":arch_id,
              "family":family,"class":kind,"word_bits":bits,"encoding_model":encoding,"source_ref":source,
              "candidate_status":"discovery-only","native_mode":{"status":"not-implemented"},
              "compatibility_mode":{"status":"not-implemented"},"verified_instruction_forms":0,
              "binary_formats":["elf","pe-coff","mach-o","raw","ncb"],
              "note":"Architecture inventory entry only; no instruction form or executable semantics are implied."})
            continue
        for row in forms:
            _, mnemonic, form_id, operands, syntax, length_bits, value_bits, mask_bits=row[:8]
            op=normalize(mnemonic); sem=OPS.get(op)
            candidates.append({"id":f"insn:{arch_id}:{op}:{form_id}","kind":"instruction-candidate",
              "architecture":arch_id,"family":family,"class":kind,"word_bits":bits,"mnemonic":mnemonic,
              "form_id":form_id,"operands":operands,"syntax":syntax,"length_bits":length_bits,
              "value_bits":value_bits,"mask_bits":mask_bits,"encoding_model":encoding,"source_ref":source,
              "semantic_operation":sem[0] if sem else None,
              "candidate_status":"catalogued-unverified",
              "native_mode":{"status":"reference-micro-op" if sem else "not-implemented",
                "chimera_equivalent":sem[0] if sem else None},
              "compatibility_mode":{"status":"reference-interpreter" if sem else "unsupported",
                "execution_semantics":"deterministic integer semantics; architectural side effects not modeled" if sem else None},
              "binary_formats":["raw","elf","pe-coff","mach-o","ncb"],
              "conformance_status":"not-tested",
              "note":"Encoding candidate only; database presence is not proof of ISA conformance."})
    return candidates

def refresh(db):
    db["execution_model"]={"schema":"CHIMERA-ISA-EXECUTION-CANDIDATES-1",
      "policy":"Discovery candidates are not conformance claims. Only operations implemented in the reference interpreter are executable here.",
      "modes":{"native":"maps supported guest operations to Chimera semantic micro-ops; this is not machine-code JIT output",
       "compatibility":"interprets supported integer operations using deterministic reference semantics"},
      "binary_formats":FORMATS,
      "execution_candidates":build_candidates(db)}
    return db

def execute(args):
    db=load_db()
    arch=args.arch
    known=next((a for a in db["architectures"] if a and a[0]==arch),None)
    if not known: raise ValueError(f"unknown architecture: {arch}")
    mnemonic=normalize(args.mnemonic)
    forms=[row for row in db["instructions"] if len(row)>=8 and row[0]==arch and normalize(row[1])==mnemonic]
    if not forms:
        raise NotImplementedError(f"{arch}:{mnemonic} is not present as an instruction form in the canonical database")
    op=OPS.get(mnemonic)
    if not op: raise NotImplementedError(f"{arch}:{mnemonic} has no implemented reference semantics")
    bits=int(known[3] or ARCH_BITS.get(arch,64))
    if bits<1 or bits>65536: raise ValueError(f"unsupported register width: {bits}")
    if args.mode=="native":
        return {"architecture":arch,"mode":"native-mapping","executed":False,
          "mnemonic":mnemonic,"semantic_operation":op[0],"register_width_bits":bits,
          "native_mapping":{"target":"Chimera semantic micro-op","operation":op[0]},
          "note":"Mapping metadata only. This tool does not generate or execute native machine code."}
    mask=(1<<bits)-1
    lhs=args.lhs; rhs=args.rhs
    if mnemonic in {"MOV","MV","LI","LUI","NOP","HINT"}: rhs=0
    result=op[1](lhs,rhs,bits)&mask
    return {"architecture":arch,"mode":args.mode,"mnemonic":mnemonic,
      "semantic_operation":op[0],"inputs":{"lhs":lhs,"rhs":rhs},"result":result,
      "register_width_bits":bits,"native_mapping":{"target":"Chimera semantic micro-op","operation":op[0]},
      "compatibility":{"executed":True,"model":"integer reference semantics"},
      "limitations":["No guest byte-stream decoding in this command","No flags, memory, exceptions, privilege state, MMU, devices, or timing model",
       "Result is masked to target register width","Not an ISA conformance test"]}

# A real, bounded RV32I instruction-word decoder/executor for the base integer
# ALU and upper-immediate forms. This operates on one 32-bit instruction word;
# it is not a complete RV32I machine (no branches, loads/stores, traps, CSR, or devices).
RV32I_ALU_R = {
    (0x0, 0x00): "ADD", (0x0, 0x20): "SUB",
    (0x7, 0x00): "AND", (0x6, 0x00): "OR", (0x4, 0x00): "XOR",
    (0x1, 0x00): "SLL", (0x5, 0x00): "SRL", (0x5, 0x20): "SRA",
}
RV32I_ALU_I = {
    0x0: "ADDI", 0x7: "ANDI", 0x6: "ORI", 0x4: "XORI",
    0x1: "SLLI", 0x5: "SRLI", # SRAI is selected by funct7=0x20 below.
}

def _sign_extend(value, bits):
    sign = 1 << (bits - 1)
    return (value ^ sign) - sign

def decode_rv32i(word):
    """Decode one RV32I base integer ALU/upper-immediate instruction word.

    Returns normalized fields or raises ValueError for illegal/unsupported encodings.
    """
    if not isinstance(word, int) or word < 0 or word > 0xffffffff:
        raise ValueError("instruction word must be an unsigned 32-bit integer")
    opcode = word & 0x7f
    rd = (word >> 7) & 0x1f
    funct3 = (word >> 12) & 0x7
    rs1 = (word >> 15) & 0x1f
    rs2 = (word >> 20) & 0x1f
    funct7 = (word >> 25) & 0x7f
    if opcode == 0x33:
        key = (funct3, funct7)
        if key not in RV32I_ALU_R:
            raise ValueError(f"illegal or unsupported RV32I R-type encoding funct3=0x{funct3:x} funct7=0x{funct7:x}")
        return {"mnemonic": RV32I_ALU_R[key], "rd": rd, "rs1": rs1, "rs2": rs2, "immediate": None, "length_bits": 32}
    if opcode == 0x13:
        if funct3 == 0x1:
            if funct7 != 0:
                raise ValueError("illegal SLLI encoding: upper immediate bits must be zero in RV32I")
            mnemonic = "SLLI"
            imm = rs2
        elif funct3 == 0x5:
            if funct7 == 0:
                mnemonic, imm = "SRLI", rs2
            elif funct7 == 0x20:
                mnemonic, imm = "SRAI", rs2
            else:
                raise ValueError("illegal SRLI/SRAI encoding: reserved upper immediate bits")
        else:
            mnemonic = RV32I_ALU_I.get(funct3)
            if mnemonic is None:
                raise ValueError(f"unsupported RV32I I-type ALU funct3=0x{funct3:x}")
            imm = _sign_extend((word >> 20) & 0xfff, 12)
        return {"mnemonic": mnemonic, "rd": rd, "rs1": rs1, "rs2": None, "immediate": imm, "length_bits": 32}
    if opcode == 0x37:
        return {"mnemonic": "LUI", "rd": rd, "rs1": None, "rs2": None, "immediate": word & 0xfffff000, "length_bits": 32}
    if opcode == 0x17:
        return {"mnemonic": "AUIPC", "rd": rd, "rs1": None, "rs2": None, "immediate": word & 0xfffff000, "length_bits": 32}
    raise ValueError(f"opcode 0x{opcode:02x} is outside the implemented RV32I decoder subset")

def step_rv32i(word, registers=None, pc=0):
    """Execute one decoded RV32I ALU/upper-immediate instruction in 32-bit state."""
    decoded = decode_rv32i(word)
    regs = [0] * 32 if registers is None else list(registers)
    if len(regs) != 32 or any(not isinstance(v, int) for v in regs):
        raise ValueError("register state must contain exactly 32 integer values")
    regs = [v & 0xffffffff for v in regs]
    old_pc = pc & 0xffffffff
    name, rd, rs1, rs2, imm = (decoded[k] for k in ("mnemonic", "rd", "rs1", "rs2", "immediate"))
    a = regs[rs1] if rs1 is not None else 0
    b = regs[rs2] if rs2 is not None else (imm if imm is not None else 0)
    if name in ("ADD", "ADDI"): value = a + b
    elif name == "SUB": value = a - b
    elif name in ("AND", "ANDI"): value = a & b
    elif name in ("OR", "ORI"): value = a | b
    elif name in ("XOR", "XORI"): value = a ^ b
    elif name in ("SLL", "SLLI"): value = a << (b & 31)
    elif name in ("SRL", "SRLI"): value = a >> (b & 31)
    elif name in ("SRA", "SRAI"): value = _sign_extend(a, 32) >> (b & 31)
    elif name == "LUI": value = imm
    elif name == "AUIPC": value = old_pc + imm
    else: raise ValueError(f"no RV32I execution semantics for {name}")
    if rd != 0: regs[rd] = value & 0xffffffff
    regs[0] = 0
    return {"architecture":"riscv32", "mode":"rv32i-single-step", "instruction_word":f"0x{word:08x}",
      "decoded":decoded, "pc_before":old_pc, "pc_after":(old_pc + 4) & 0xffffffff,
      "registers":regs, "rd_value":regs[rd], "executed":True,
      "limitations":["ALU and upper-immediate subset only", "No branch/jump, load/store, exception, CSR, privilege, MMU, device, or interrupt semantics", "Not a complete RV32I implementation or official conformance result"]}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest="command",required=True)
    ls=sub.add_parser("list",help="list architectures or instruction candidates")
    ls.add_argument("--arch")
    ls.add_argument("--supported-only",action="store_true")
    ls.add_argument("--json",action="store_true")
    ins=sub.add_parser("inspect",help="inspect an architecture's candidates")
    ins.add_argument("arch")
    run=sub.add_parser("run",help="execute one supported reference instruction")
    run.add_argument("--arch",required=True)
    run.add_argument("--mnemonic",required=True)
    run.add_argument("--lhs",type=int,default=0)
    run.add_argument("--rhs",type=int,default=0)
    run.add_argument("--mode",choices=("native","compatibility"),default="compatibility")
    fmt=sub.add_parser("formats",help="describe supported binary container families")
    fmt.add_argument("--json",action="store_true")
    step=sub.add_parser("step-rv32i",help="decode and execute one RV32I ALU/upper-immediate instruction word")
    step.add_argument("--word",required=True,type=lambda s:int(s,0),help="32-bit instruction word, e.g. 0x002081b3")
    step.add_argument("--registers",default=None,help="optional JSON array of 32 integer registers")
    step.add_argument("--pc",type=lambda s:int(s,0),default=0,help="program counter (integer or 0x-prefixed)")
    refresh_parser=sub.add_parser("refresh-db",help="rebuild execution_candidates metadata in canonical ISA database")
    args=ap.parse_args(); db=load_db()
    if args.command=="refresh-db":
        db=refresh(db); DB_PATH.write_text(json.dumps(db,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print(f"updated {DB_PATH}: {len(db['execution_model']['execution_candidates'])} candidates")
        return 0
    if args.command=="formats":
        data=FORMATS
        print(json.dumps(data,indent=2) if args.json else "\n".join(f"{k}: {v['description']}" for k,v in data.items()))
        return 0
    candidates=build_candidates(db)
    if args.command=="list":
        rows=[x for x in candidates if (not args.arch or x["architecture"]==args.arch)]
        if args.supported_only: rows=[x for x in rows if x.get("native_mode",{}).get("status")=="reference-micro-op"]
        print(json.dumps(rows,indent=2,ensure_ascii=False) if args.json else "\n".join(f"{x['id']} [{x['native_mode']['status']}] {x.get('syntax',x.get('family',''))}" for x in rows))
        return 0
    if args.command=="inspect":
        rows=[x for x in candidates if x["architecture"]==args.arch]
        print(json.dumps({"architecture":args.arch,"candidate_count":len(rows),"candidates":rows},indent=2,ensure_ascii=False))
        return 0
    if args.command=="run":
        try: result=execute(args)
        except (ValueError,NotImplementedError) as exc:
            print(f"ISA candidate execution refused: {exc}",file=sys.stderr); return 2
        print(json.dumps(result,indent=2)); return 0
    if args.command=="step-rv32i":
        try:
            registers=json.loads(args.registers) if args.registers is not None else None
            result=step_rv32i(args.word,registers,args.pc)
        except (ValueError,TypeError,json.JSONDecodeError) as exc:
            print(f"RV32I step refused: {exc}",file=sys.stderr); return 2
        print(json.dumps(result,indent=2)); return 0
    return 2

if __name__=="__main__":
    raise SystemExit(main())
