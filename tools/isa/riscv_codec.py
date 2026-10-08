#!/usr/bin/env python3
"""Chimera ISA tooling: executable RV32I subset codec and interpreter.

This is deliberately a tested subset, not a claim of full RISC-V or universal ISA support.
"""
import argparse
import json
import re
import sys

MASK32 = 0xFFFFFFFF
REG = re.compile(r"^[xX](\d+)$")


def reg(text):
    m = REG.match(text.strip())
    if not m or int(m.group(1)) > 31:
        raise ValueError("register must be x0..x31")
    return int(m.group(1))


def signed(value, bits):
    value &= (1 << bits) - 1
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def encode(line):
    line = line.split("#", 1)[0].strip()
    if not line:
        raise ValueError("empty instruction")
    parts = line.replace(",", " ").replace("(", " ").replace(")", "").split()
    op = parts[0].upper()
    a = parts[1:]
    r_ops = {"ADD": (0, 0), "SUB": (0x20, 0), "SLL": (0, 1), "SLT": (0, 2),
             "SLTU": (0, 3), "XOR": (0, 4), "SRL": (0, 5), "SRA": (0x20, 5),
             "OR": (0, 6), "AND": (0, 7)}
    i_ops = {"ADDI": 0, "SLTI": 2, "SLTIU": 3, "XORI": 4, "ORI": 6, "ANDI": 7}
    loads = {"LB": (0, 8), "LH": (1, 16), "LW": (2, 32), "LBU": (4, 8), "LHU": (5, 16)}
    stores = {"SB": 0, "SH": 1, "SW": 2}
    branches = {"BEQ": 0, "BNE": 1, "BLT": 4, "BGE": 5, "BLTU": 6, "BGEU": 7}
    if op in r_ops and len(a) == 3:
        rd, rs1, rs2 = map(reg, a)
        f7, f3 = r_ops[op]
        return (f7 << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | 0x33
    if op in i_ops and len(a) == 3:
        rd, rs1 = reg(a[0]), reg(a[1]); imm = int(a[2], 0)
        if not -2048 <= imm <= 2047: raise ValueError("12-bit immediate out of range")
        return ((imm & 0xFFF) << 20) | (rs1 << 15) | (i_ops[op] << 12) | (rd << 7) | 0x13
    if op in loads and len(a) == 3:
        rd, imm, rs1 = reg(a[0]), int(a[1], 0), reg(a[2])
        if not -2048 <= imm <= 2047: raise ValueError("12-bit offset out of range")
        f3, _ = loads[op]
        return ((imm & 0xFFF) << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | 0x03
    if op in stores and len(a) == 3:
        rs2, imm, rs1 = reg(a[0]), int(a[1], 0), reg(a[2])
        if not -2048 <= imm <= 2047: raise ValueError("12-bit offset out of range")
        imm &= 0xFFF; f3 = stores[op]
        return ((imm >> 5) << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | ((imm & 31) << 7) | 0x23
    if op in branches and len(a) == 3:
        rs1, rs2, imm = reg(a[0]), reg(a[1]), int(a[2], 0)
        if imm % 2 or not -4096 <= imm <= 4094: raise ValueError("branch offset must be even and within range")
        u = imm & 0x1FFF; f3 = branches[op]
        return (((u >> 12) & 1) << 31) | (((u >> 5) & 0x3F) << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (((u >> 1) & 0xF) << 8) | (((u >> 11) & 1) << 7) | 0x63
    if op == "JAL" and len(a) in (1, 2):
        rd, imm = (reg(a[0]), int(a[1], 0)) if len(a) == 2 else (1, int(a[0], 0))
        if imm % 2 or not -(1 << 20) <= imm < (1 << 20): raise ValueError("JAL offset must be even and within range")
        u = imm & 0x1FFFFF
        return (((u >> 20) & 1) << 31) | (((u >> 1) & 0x3FF) << 21) | (((u >> 11) & 1) << 20) | (((u >> 12) & 0xFF) << 12) | (rd << 7) | 0x6F
    if op in ("ECALL", "EBREAK") and not a:
        return 0x00000073 if op == "ECALL" else 0x00100073
    raise ValueError("unsupported instruction or operand shape in RV32I codec subset: " + line)


def decode(word):
    w = int(word, 0) if isinstance(word, str) else int(word)
    if not 0 <= w <= MASK32: raise ValueError("instruction must be a 32-bit word")
    op, rd, f3, rs1, rs2, f7 = w & 0x7F, (w >> 7) & 31, (w >> 12) & 7, (w >> 15) & 31, (w >> 20) & 31, (w >> 25) & 0x7F
    if w == 0x73: return "ECALL"
    if w == 0x00100073: return "EBREAK"
    if op == 0x33:
        names = {(0,0):"ADD",(0x20,0):"SUB",(0,1):"SLL",(0,2):"SLT",(0,3):"SLTU",(0,4):"XOR",(0,5):"SRL",(0x20,5):"SRA",(0,6):"OR",(0,7):"AND"}
        if (f7,f3) not in names: raise ValueError("unknown R-type encoding")
        return f"{names[(f7,f3)]} x{rd}, x{rs1}, x{rs2}"
    if op == 0x13:
        names = {0:"ADDI",2:"SLTI",3:"SLTIU",4:"XORI",6:"ORI",7:"ANDI"}
        if f3 not in names: raise ValueError("unsupported I-type encoding")
        return f"{names[f3]} x{rd}, x{rs1}, {signed(w >> 20,12)}"
    if op == 0x03:
        names={0:"LB",1:"LH",2:"LW",4:"LBU",5:"LHU"}
        if f3 not in names: raise ValueError("unknown load encoding")
        return f"{names[f3]} x{rd}, {signed(w >> 20,12)}(x{rs1})"
    if op == 0x23:
        imm=signed(((w >> 25) << 5) | ((w >> 7) & 31),12); names={0:"SB",1:"SH",2:"SW"}
        if f3 not in names: raise ValueError("unknown store encoding")
        return f"{names[f3]} x{rs2}, {imm}(x{rs1})"
    if op == 0x63:
        names={0:"BEQ",1:"BNE",4:"BLT",5:"BGE",6:"BLTU",7:"BGEU"}
        if f3 not in names: raise ValueError("unknown branch encoding")
        imm=signed((((w>>31)&1)<<12)|(((w>>7)&1)<<11)|(((w>>25)&0x3F)<<5)|(((w>>8)&0xF)<<1),13)
        return f"{names[f3]} x{rs1}, x{rs2}, {imm}"
    if op == 0x6F:
        imm=signed((((w>>31)&1)<<20)|(((w>>12)&0xFF)<<12)|(((w>>20)&1)<<11)|(((w>>21)&0x3FF)<<1),21)
        return f"JAL x{rd}, {imm}"
    raise ValueError("unsupported/illegal instruction encoding")


def execute(program, max_steps=10000):
    """Tiny RV32I interpreter for register arithmetic and control flow; no memory/MMU/devices."""
    regs=[0]*32; pc=0; steps=0
    while 0 <= pc < len(program) and steps < max_steps:
        ins=decode(program[pc]); parts=ins.replace(",","").split(); op=parts[0]; oldpc=pc; pc+=1; steps+=1
        if op in ("ECALL","EBREAK"): break
        if op in ("ADD","SUB","AND","OR","XOR","SLL","SRL","SRA","SLT","SLTU"):
            rd,a,b=map(lambda x:int(x[1:]),parts[1:]); x,y=regs[a],regs[b]
            val={"ADD":x+y,"SUB":x-y,"AND":x&y,"OR":x|y,"XOR":x^y,"SLL":x<<(y&31),"SRL":(x&MASK32)>>(y&31),"SRA":signed(x,32)>>(y&31),"SLT":int(signed(x,32)<signed(y,32)),"SLTU":int((x&MASK32)<(y&MASK32))}[op]
            regs[rd]=val&MASK32
        elif op in ("ADDI","XORI","ORI","ANDI","SLTI","SLTIU"):
            rd=int(parts[1][1:]); a=int(parts[2][1:]); imm=int(parts[3]); x=regs[a]
            val={"ADDI":x+imm,"XORI":x^imm,"ORI":x|imm,"ANDI":x&imm,"SLTI":int(signed(x,32)<imm),"SLTIU":int((x&MASK32)<(imm&MASK32))}[op]; regs[rd]=val&MASK32
        elif op in ("BEQ","BNE","BLT","BGE","BLTU","BGEU"):
            a,b,off=int(parts[1][1:]),int(parts[2][1:]),int(parts[3]); x,y=regs[a],regs[b]
            cond={"BEQ":x==y,"BNE":x!=y,"BLT":signed(x,32)<signed(y,32),"BGE":signed(x,32)>=signed(y,32),"BLTU":x<y,"BGEU":x>=y}[op]
            if cond: pc=oldpc+off//4
        elif op=="JAL":
            rd,off=int(parts[1][1:]),int(parts[2]); regs[rd]=pc*4; pc=oldpc+off//4
        else: raise ValueError("interpreter currently supports arithmetic/control-flow subset only: "+op)
        regs[0]=0
    return {"pc":pc*4,"steps":steps,"registers":regs,"halted":pc<0 or pc>=len(program) or (steps and decode(program[min(max(pc-1,0),len(program)-1)]) in ("ECALL","EBREAK"))}


def encode(line):
    """Strict RV32I base encoder (extensions intentionally excluded)."""
    line = line.split("#", 1)[0].strip()
    if not line:
        raise ValueError("empty instruction")
    parts = line.replace(",", " ").replace("(", " ").replace(")", "").split()
    op, a = parts[0].upper(), parts[1:]
    def imm(v, lo, hi, what):
        n = int(v, 0)
        if not lo <= n <= hi: raise ValueError(f"{what} out of range")
        return n
    r = {"ADD":(0,0),"SUB":(32,0),"SLL":(0,1),"SLT":(0,2),"SLTU":(0,3),"XOR":(0,4),"SRL":(0,5),"SRA":(32,5),"OR":(0,6),"AND":(0,7)}
    ii = {"ADDI":0,"SLTI":2,"SLTIU":3,"XORI":4,"ORI":6,"ANDI":7}
    loads={"LB":(0,1),"LH":(1,2),"LW":(2,4),"LBU":(4,1),"LHU":(5,2)}
    stores={"SB":0,"SH":1,"SW":2}
    branches={"BEQ":0,"BNE":1,"BLT":4,"BGE":5,"BLTU":6,"BGEU":7}
    if op in r and len(a)==3:
        rd,rs1,rs2=map(reg,a); f7,f3=r[op]
        return (f7<<25)|(rs2<<20)|(rs1<<15)|(f3<<12)|(rd<<7)|0x33
    if op in ii and len(a)==3:
        rd,rs1=reg(a[0]),reg(a[1]); n=imm(a[2],-2048,2047,"12-bit immediate")
        return ((n&0xfff)<<20)|(rs1<<15)|(ii[op]<<12)|(rd<<7)|0x13
    if op in ("SLLI","SRLI","SRAI") and len(a)==3:
        rd,rs1=reg(a[0]),reg(a[1]); sh=imm(a[2],0,31,"shift amount")
        f3={"SLLI":1,"SRLI":5,"SRAI":5}[op]; f7=32 if op=="SRAI" else 0
        return (f7<<25)|(sh<<20)|(rs1<<15)|(f3<<12)|(rd<<7)|0x13
    if op in loads and len(a)==3:
        rd,off,rs1=reg(a[0]),imm(a[1],-2048,2047,"load offset"),reg(a[2]); f3,_=loads[op]
        return ((off&0xfff)<<20)|(rs1<<15)|(f3<<12)|(rd<<7)|3
    if op in stores and len(a)==3:
        rs2,off,rs1=reg(a[0]),imm(a[1],-2048,2047,"store offset"),reg(a[2]); u=off&0xfff; f3=stores[op]
        return ((u>>5)<<25)|(rs2<<20)|(rs1<<15)|(f3<<12)|((u&31)<<7)|0x23
    if op in branches and len(a)==3:
        rs1,rs2=reg(a[0]),reg(a[1]); off=imm(a[2],-4096,4094,"branch offset")
        if off&1: raise ValueError("branch offset must be even")
        u=off&0x1fff
        return (((u>>12)&1)<<31)|(((u>>5)&63)<<25)|(rs2<<20)|(rs1<<15)|(branches[op]<<12)|(((u>>1)&15)<<8)|(((u>>11)&1)<<7)|0x63
    if op in ("LUI","AUIPC") and len(a)==2:
        rd=reg(a[0]); n=imm(a[1],-(1<<19),(1<<20)-1,"U-immediate")
        return ((n&0xfffff)<<12)|(rd<<7)|(0x37 if op=="LUI" else 0x17)
    if op=="JALR" and len(a)==3:
        rd,rs1=reg(a[0]),reg(a[2]); n=imm(a[1],-2048,2047,"JALR immediate")
        return ((n&0xfff)<<20)|(rs1<<15)|(rd<<7)|0x67
    if op=="JAL" and len(a) in (1,2):
        rd,off=(reg(a[0]),imm(a[1],-(1<<20),(1<<20)-2,"JAL offset")) if len(a)==2 else (1,imm(a[0],-(1<<20),(1<<20)-2,"JAL offset"))
        if off&1: raise ValueError("JAL offset must be even")
        u=off&0x1fffff
        return (((u>>20)&1)<<31)|(((u>>1)&0x3ff)<<21)|(((u>>11)&1)<<20)|(((u>>12)&0xff)<<12)|(rd<<7)|0x6f
    if op=="FENCE" and len(a) in (0,2):
        # Base FENCE supports predecessor/successor sets; rd and rs1 are zero.
        pred,succ=(int(a[0],0),int(a[1],0)) if a else (15,15)
        if pred<0 or pred>15 or succ<0 or succ>15: raise ValueError("FENCE sets must be 4-bit masks")
        return (pred<<24)|(succ<<20)|0x0f
    if op in ("ECALL","EBREAK") and not a: return 0x73 if op=="ECALL" else 0x00100073
    raise ValueError("unsupported instruction or operand shape: "+line)


def decode(word):
    """Strict RV32I decoder; reserved funct fields and extension opcodes trap."""
    w = int(word,0) if isinstance(word,str) else int(word)
    if not 0 <= w <= MASK32: raise ValueError("instruction must be a 32-bit word")
    op,rd,f3,rs1,rs2,f7=w&127,(w>>7)&31,(w>>12)&7,(w>>15)&31,(w>>20)&31,w>>25
    si=lambda v,b:signed(v,b)
    if w==0x73:return "ECALL"
    if w==0x00100073:return "EBREAK"
    if op in (0x37,0x17): return f"{'LUI' if op==0x37 else 'AUIPC'} x{rd}, 0x{(w>>12):05X}"
    if op==0x33:
        names={(0,0):"ADD",(32,0):"SUB",(0,1):"SLL",(0,2):"SLT",(0,3):"SLTU",(0,4):"XOR",(0,5):"SRL",(32,5):"SRA",(0,6):"OR",(0,7):"AND"}
        if (f7,f3) not in names: raise ValueError("reserved R-type encoding")
        return f"{names[f7,f3]} x{rd}, x{rs1}, x{rs2}"
    if op==0x13:
        if f3 in (1,5):
            if f3==1 and f7==0: name="SLLI"
            elif f3==5 and f7==0: name="SRLI"
            elif f3==5 and f7==32: name="SRAI"
            else: raise ValueError("reserved shift-immediate encoding")
            return f"{name} x{rd}, x{rs1}, {rs2}"
        names={0:"ADDI",2:"SLTI",3:"SLTIU",4:"XORI",6:"ORI",7:"ANDI"}
        if f3 not in names: raise ValueError("reserved OP-IMM encoding")
        return f"{names[f3]} x{rd}, x{rs1}, {si(w>>20,12)}"
    if op==3:
        names={0:"LB",1:"LH",2:"LW",4:"LBU",5:"LHU"}
        if f3 not in names: raise ValueError("reserved load encoding")
        return f"{names[f3]} x{rd}, {si(w>>20,12)}(x{rs1})"
    if op==0x23:
        names={0:"SB",1:"SH",2:"SW"}
        if f3 not in names: raise ValueError("reserved store encoding")
        return f"{names[f3]} x{rs2}, {si(((w>>25)<<5)|((w>>7)&31),12)}(x{rs1})"
    if op==0x63:
        names={0:"BEQ",1:"BNE",4:"BLT",5:"BGE",6:"BLTU",7:"BGEU"}
        if f3 not in names: raise ValueError("reserved branch encoding")
        n=si((((w>>31)&1)<<12)|(((w>>7)&1)<<11)|(((w>>25)&63)<<5)|(((w>>8)&15)<<1),13)
        return f"{names[f3]} x{rs1}, x{rs2}, {n}"
    if op==0x6f:
        n=si((((w>>31)&1)<<20)|(((w>>12)&255)<<12)|(((w>>20)&1)<<11)|(((w>>21)&1023)<<1),21)
        return f"JAL x{rd}, {n}"
    if op==0x67 and f3==0: return f"JALR x{rd}, {si(w>>20,12)}(x{rs1})"
    if op==0x0f and f3==0 and rd==0 and rs1==0 and ((w>>28)&15)==0:
        return f"FENCE {(w>>24)&15}, {(w>>20)&15}"
    raise ValueError("unsupported/illegal RV32I encoding")


def execute(program, max_steps=10000):
    """Execute through the shared RV32Machine, not a second interpreter."""
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from rv32_machine import RV32Machine
    if max_steps < 1:
        raise ValueError("max_steps must be positive")
    if any(not isinstance(word, int) or not 0 <= word <= MASK32 for word in program):
        raise ValueError("program words must be unsigned 32-bit integers")
    machine = RV32Machine(memory_size=max(65536, len(program) * 4 + 16))
    machine.load(0, b"".join(word.to_bytes(4, "little") for word in program))
    result = machine.run(max_steps=max_steps)
    result["halted"] = bool(result["halted"])
    result["engine"] = "RV32Machine"
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest="cmd",required=True)
    e=sub.add_parser("encode"); e.add_argument("instruction")
    d=sub.add_parser("decode"); d.add_argument("word")
    x=sub.add_parser("run"); x.add_argument("words",nargs="+"); x.add_argument("--max-steps",type=int,default=10000)
    a=p.parse_args()
    try:
        if a.cmd=="encode": print(f"0x{encode(a.instruction):08X}")
        elif a.cmd=="decode": print(decode(a.word))
        else: print(json.dumps(execute([int(v,0) for v in a.words],a.max_steps),indent=2))
    except (ValueError,KeyError) as exc:
        print("error:",exc,file=sys.stderr); return 2
    return 0
if __name__=="__main__": raise SystemExit(main())
