#!/usr/bin/env python3
"""
Chimera II — 8192-bit CPU Research Emulator
Imported from the ChatGPT Library as a reference artifact.

This is a research/reference implementation. It models 8192-bit operands and
RISC/CISC encodings; it is not a claim of existing 8192-bit silicon.
"""
from __future__ import annotations
import argparse, struct, sys, time
from dataclasses import dataclass
from enum import IntEnum

WORD_BITS = 8192
WORD_BYTES = 1024
WORD_MASK = (1 << WORD_BITS) - 1
ADDR_MASK = (1 << 64) - 1
GPRS, PREDS, VREGS = 32, 16, 16
VCORE_COUNT = 8
MMIO_BASE = 0xFFFF_0000_0000_0000
MMIO_LIMIT = 0xFFFF_0000_1000_0000
UART_TX = MMIO_BASE

try:
    import numpy as np
except Exception:
    np = None
try:
    import tensorflow as tf
except Exception:
    tf = None
try:
    import torch
except Exception:
    torch = None

def u8192(x: int) -> int:
    return x & WORD_MASK

def s8192(x: int) -> int:
    x &= WORD_MASK
    return x - (1 << WORD_BITS) if x & (1 << (WORD_BITS - 1)) else x

def reg(s: str, prefix: str, count: int) -> int:
    s = s.upper().strip()
    if not s.startswith(prefix):
        raise ValueError(f"expected {prefix} register: {s}")
    n = int(s[len(prefix):])
    if not 0 <= n < count:
        raise ValueError(f"register out of range: {s}")
    return n

class Op(IntEnum):
    NOP=0x00; HALT=0x01; MOVI=0x02; MOV=0x03
    ADD=0x10; SUB=0x11; MUL=0x12; DIV=0x13; MOD=0x14
    AND=0x20; OR=0x21; XOR=0x22; NOT=0x23; SHL=0x24; SHR=0x25; SAR=0x26
    LOAD=0x30; STORE=0x31; LDX=0x32; STX=0x33
    CMP=0x40; CMPI=0x41; BEQ=0x42; BNE=0x43; BLT=0x44; BGT=0x45
    JMP=0x46; CALL=0x47; RET=0x48
    PUSH=0x50; POP=0x51
    CAS=0x60; FENCE=0x61; FLUSH=0x62; INVL=0x63
    VADD=0x70; VMUL=0x71; VXOR=0x72; VDOT=0x73; VLOAD=0x74; VSTORE=0x75
    DMA_COPY=0x80; NET_TX=0x81; NET_RX=0x82
    SYS=0x90

@dataclass
class Ins:
    op: Op
    rd: int=0; rs1: int=0; rs2: int=0
    imm: int=0; size: int=0; pred: int=-1

RISC_BYTES = 32

class RISC:
    @staticmethod
    def enc(i: Ins) -> bytes:
        b=bytearray(RISC_BYTES)
        b[0]=i.op; b[1]=i.rd; b[2]=i.rs1; b[3]=i.rs2
        b[4]=255 if i.pred < 0 else i.pred
        struct.pack_into("<q", b, 5, i.imm)
        struct.pack_into("<H", b, 13, i.size & 0xffff)
        return bytes(b)
    @staticmethod
    def dec(b: bytes) -> Ins:
        if len(b)<RISC_BYTES: raise ValueError("truncated RISC instruction")
        return Ins(Op(b[0]), b[1], b[2], b[3], struct.unpack_from("<q",b,5)[0], struct.unpack_from("<H",b,13)[0], -1 if b[4]==255 else b[4])

class CISC:
    @staticmethod
    def enc(i: Ins) -> bytes:
        f=0; x=[bytes((int(i.op),0))]
        if i.rd: f|=1; x.append(bytes((i.rd,)))
        if i.rs1: f|=2; x.append(bytes((i.rs1,)))
        if i.rs2: f|=4; x.append(bytes((i.rs2,)))
        if i.imm: f|=8; x.append(struct.pack("<q",i.imm))
        if i.size: f|=16; x.append(struct.pack("<H",i.size))
        if i.pred>=0: f|=32; x.append(bytes((i.pred,)))
        x[0]=bytes((int(i.op),f))
        return b"".join(x)
    @staticmethod
    def dec(b: bytes):
        if len(b)<2: raise ValueError("truncated CISC instruction")
        op=Op(b[0]); f=b[1]; p=2
        def take():
            nonlocal p
            if p>=len(b): raise ValueError("truncated field")
            v=b[p]; p+=1; return v
        rd=take() if f&1 else 0; rs1=take() if f&2 else 0; rs2=take() if f&4 else 0
        imm=struct.unpack_from("<q",b,p)[0] if f&8 else 0
        if f&8: p+=8
        size=struct.unpack_from("<H",b,p)[0] if f&16 else 0
        if f&16: p+=2
        pred=take() if f&32 else -1
        return Ins(op,rd,rs1,rs2,imm,size,pred),p

def toks(s: str):
    out=[]; cur=""; d=0
    for c in s:
        if c=="[": d+=1
        if c=="]": d-=1
        if c=="," and d==0:
            out.append(cur.strip()); cur=""
        else: cur+=c
    if cur.strip(): out.append(cur.strip())
    return out

def integer(s: str): return int(s.strip(),0)

class Assembler:
    def __init__(self, mode="risc"): self.mode=mode.lower()
    def clean(self,s): return s.split("#",1)[0].split(";",1)[0].strip()
    def mem(self,s):
        z=s.strip()
        if not (z.startswith("[") and z.endswith("]")): raise ValueError(z)
        z=z[1:-1].replace(" ","")
        for sep in ("+","-"):
            if sep in z[1:]:
                k=z[1:].find(sep)+1
                return reg(z[:k],"R",GPRS), integer(z[k:])
        return reg(z,"R",GPRS),0
    def imm_label(self,s,labels,pc):
        try: return integer(s)
        except ValueError:
            if s not in labels: raise ValueError(f"unknown label {s}")
            return labels[s]-pc
    def parse(self,line,labels,pc):
        a=toks(line); name=a[0].upper(); q=a[1:]
        op=Op[name]
        R=lambda x:reg(x,"R",GPRS)
        if op in (Op.NOP,Op.HALT,Op.RET,Op.FENCE,Op.FLUSH,Op.INVL): return Ins(op)
        if op==Op.MOVI: return Ins(op,rd=R(q[0]),imm=self.imm_label(q[1],labels,pc))
        if op==Op.MOV: return Ins(op,rd=R(q[0]),rs1=R(q[1]))
        if op in (Op.ADD,Op.SUB,Op.MUL,Op.DIV,Op.MOD,Op.AND,Op.OR,Op.XOR,Op.SHL,Op.SHR,Op.SAR,Op.CMP): return Ins(op,R(q[0]),R(q[1]),R(q[2]))
        if op==Op.NOT: return Ins(op,R(q[0]),R(q[1]))
        if op==Op.CMPI: return Ins(op,rs1=R(q[0]),imm=self.imm_label(q[1],labels,pc))
        if op in (Op.BEQ,Op.BNE,Op.BLT,Op.BGT): return Ins(op,rs1=R(q[0]),rs2=R(q[1]),imm=self.imm_label(q[2],labels,pc))
        if op in (Op.JMP,Op.CALL): return Ins(op,imm=self.imm_label(q[0],labels,pc))
        if op in (Op.LOAD,Op.STORE,Op.LDX,Op.STX):
            base,off=self.mem(q[1]); size=integer(q[2]) if len(q)>2 else WORD_BYTES
            return Ins(op,rd=R(q[0]) if op in (Op.LOAD,Op.LDX) else 0,rs1=base,rs2=R(q[0]) if op in (Op.STORE,Op.STX) else 0,imm=off,size=size if op in (Op.LDX,Op.STX) else 0)
        if op in (Op.PUSH,Op.POP): return Ins(op,rs1=R(q[0]))
        if op==Op.CAS: return Ins(op,R(q[0]),R(q[1]),R(q[2]))
        if op in (Op.VADD,Op.VMUL,Op.VXOR,Op.VDOT): return Ins(op,reg(q[0],"V",VREGS),reg(q[1],"V",VREGS),reg(q[2],"V",VREGS))
        if op in (Op.VLOAD,Op.VSTORE):
            base,off=self.mem(q[1]); n=integer(q[2]) if len(q)>2 else WORD_BYTES
            return Ins(op,rd=reg(q[0],"V",VREGS) if op==Op.VLOAD else 0,rs1=base,rs2=reg(q[0],"V",VREGS) if op==Op.VSTORE else 0,imm=off,size=n)
        if op==Op.DMA_COPY:
            sb,so=self.mem(q[0]); db,do=self.mem(q[1])
            return Ins(op,rs1=sb,rs2=db,imm=(do<<32)|(so&0xffffffff),size=integer(q[2]))
        if op in (Op.NET_TX,Op.NET_RX):
            base,off=self.mem(q[0]); return Ins(op,rs1=base,imm=off,size=integer(q[1]))
        if op==Op.SYS: return Ins(op,imm=integer(q[0]) if q else 0)
        raise ValueError(name)
    def assemble(self,source):
        labels={}; records=[]; pc=0
        for raw in source.splitlines():
            line=self.clean(raw)
            if not line: continue
            if ":" in line:
                lab,rest=line.split(":",1); labels[lab.strip()]=pc; line=rest.strip()
                if not line: continue
            if line.lower().startswith(".org"): pc=integer(line.split()[1]); continue
            if line.lower().startswith(".byte"): n=len(toks(line.split(None,1)[1])); records.append((pc,line)); pc+=n; continue
            if line.lower().startswith(".word"): n=8*len(toks(line.split(None,1)[1])); records.append((pc,line)); pc+=n; continue
            if line.lower().startswith(".zero"): n=integer(line.split()[1]); records.append((pc,line)); pc+=n; continue
            i=self.parse(line,labels,pc); records.append((pc,line)); pc+=RISC_BYTES if self.mode=="risc" else len(CISC.enc(i))
        if not records: return b"",labels
        start=min(a for a,_ in records); blob=bytearray(pc-start)
        for a,line in records:
            if line.lower().startswith(".byte"): d=bytes(integer(x)&255 for x in toks(line.split(None,1)[1]))
            elif line.lower().startswith(".word"): d=b"".join(struct.pack("<Q",integer(x)&((1<<64)-1)) for x in toks(line.split(None,1)[1]))
            elif line.lower().startswith(".zero"): d=bytes(integer(line.split()[1]))
            else:
                i=self.parse(line,labels,a); d=RISC.enc(i) if self.mode=="risc" else CISC.enc(i)
            blob[a-start:a-start+len(d)]=d
        return bytes(blob),{k-start:v-start for k,v in labels.items()}

@dataclass
class Line:
    tag:int
    data:bytearray
    dirty:bool=False

class Cache:
    def __init__(self,mem,line=64,size=64*1024):
        self.mem=mem; self.line=line; self.lines=[None]*(size//line); self.hits=0; self.misses=0
    def parts(self,a):
        n=a//self.line; return n,n%len(self.lines),n//len(self.lines),a%self.line
    def wb(self,i):
        x=self.lines[i]
        if x and x.dirty:
            n=x.tag*len(self.lines)+i; self.mem.raw(n*self.line,bytes(x.data)); x.dirty=False
    def get(self,a):
        n,i,t,o=self.parts(a); x=self.lines[i]
        if not x or x.tag!=t:
            self.misses+=1; self.wb(i); x=Line(t,bytearray(self.mem.raw(n*self.line,self.line))); self.lines[i]=x
        else: self.hits+=1
        return x,o
    def read(self,a,n):
        out=bytearray()
        while n:
            x,o=self.get(a); k=min(n,self.line-o); out+=x.data[o:o+k]; a+=k; n-=k
        return bytes(out)
    def write(self,a,d):
        p=0
        while p<len(d):
            x,o=self.get(a); k=min(len(d)-p,self.line-o); x.data[o:o+k]=d[p:p+k]; x.dirty=True; a+=k; p+=k
    def flush(self):
        for i in range(len(self.lines)): self.wb(i)
    def invalidate(self): self.flush(); self.lines=[None]*len(self.lines)

class Memory:
    def __init__(self,size=64*1024*1024):
        self.size=size; self.buf=bytearray(size); self.mmio={}; self.cache=Cache(self)
    def check(self,a,n):
        if a<0 or a+n>self.size: raise MemoryError(f"RAM 0x{a:x}+{n}")
    def raw(self,a,n_or_data):
        if isinstance(n_or_data,int): self.check(a,n_or_data); return bytes(self.buf[a:a+n_or_data])
        d=n_or_data; self.check(a,len(d)); self.buf[a:a+len(d)]=d
    def read(self,a,n):
        a&=ADDR_MASK
        if MMIO_BASE<=a<MMIO_LIMIT: return int(self.mmio.get(a,0)).to_bytes(n,"little")
        return self.cache.read(a,n)
    def write(self,a,d):
        a&=ADDR_MASK
        if MMIO_BASE<=a<MMIO_LIMIT:
            v=int.from_bytes(d,"little"); self.mmio[a]=v
            if a==UART_TX: sys.stdout.write(chr(v&255)); sys.stdout.flush()
        else: self.cache.write(a,d)
    def load(self,a,d): self.raw(a,d); self.cache.invalidate()

@dataclass
class Desc:
    address:int
    length:int
    flags:int=0

class Ring:
    def __init__(self,n=256): self.q=[]; self.n=n
    def push(self,x):
        if len(self.q)>=self.n: return False
        self.q.append(x); return True
    def pop(self): return self.q.pop(0) if self.q else None

class TensorBackend:
    def __init__(self,name="auto"):
        avail=["numpy"] if np is not None else []
        if tf is not None: avail.append("tensorflow")
        if torch is not None: avail.append("torch")
        if name=="auto": self.name=avail[0] if avail else "python"
        elif name=="python" or name in avail: self.name=name
        else: raise RuntimeError(f"backend {name} unavailable; installed: {avail}")
    def add8192(self,a,b):
        return u8192(a+b)

@dataclass
class Flags:
    z:bool=False; n:bool=False; c:bool=False

class CPU:
    def __init__(self,mode="risc",mem=64*1024*1024,tensor="auto"):
        self.mode=mode; self.memory=Memory(mem); self.R=[0]*GPRS; self.P=[0]*PREDS; self.V=[[0]*128 for _ in range(VREGS)]
        self.pc=0; self.sp=mem-WORD_BYTES; self.lr=0; self.halted=False; self.cycles=0; self.instructions=0; self.flags=Flags()
        self.tensor=TensorBackend(tensor); self.rx=Ring(); self.tx=Ring(); self.breakpoints=set(); self.trace=False
    def r(self,n): return 0 if n==0 else self.R[n]&WORD_MASK
    def w(self,n,x):
        if n: self.R[n]=u8192(x)
    def word(self,a): return int.from_bytes(self.memory.read(a,WORD_BYTES),"little")
    def putword(self,a,x): self.memory.write(a,u8192(x).to_bytes(WORD_BYTES,"little"))
    def fetch(self):
        if self.mode=="risc": return RISC.dec(self.memory.read(self.pc,RISC_BYTES)),RISC_BYTES
        return CISC.dec(self.memory.read(self.pc,128))
    def load(self,data,base=0): self.memory.load(base,data); self.pc=base; self.halted=False
    def step(self):
        if self.halted: raise StopIteration
        if self.pc in self.breakpoints: raise RuntimeError(f"breakpoint 0x{self.pc:x}")
        i,n=self.fetch(); old=self.pc; nxt=(self.pc+n)&ADDR_MASK; op=i.op; r=self.r; w=self.w
        if self.trace: print(f"{self.cycles:08d}  {old:016x}  {op.name}")
        if op==Op.NOP: pass
        elif op==Op.HALT: self.halted=True
        elif op==Op.MOVI: w(i.rd,i.imm)
        elif op==Op.MOV: w(i.rd,r(i.rs1))
        elif op==Op.ADD: z=r(i.rs1)+r(i.rs2); self.flags.c=z>>WORD_BITS!=0; w(i.rd,z)
        elif op==Op.SUB: z=r(i.rs1)-r(i.rs2); self.flags.c=r(i.rs1)<r(i.rs2); w(i.rd,z)
        elif op==Op.MUL: w(i.rd,r(i.rs1)*r(i.rs2))
        elif op==Op.DIV:
            if not r(i.rs2): raise ZeroDivisionError
            w(i.rd,r(i.rs1)//r(i.rs2))
        elif op==Op.MOD:
            if not r(i.rs2): raise ZeroDivisionError
            w(i.rd,r(i.rs1)%r(i.rs2))
        elif op==Op.AND: w(i.rd,r(i.rs1)&r(i.rs2))
        elif op==Op.OR: w(i.rd,r(i.rs1)|r(i.rs2))
        elif op==Op.XOR: w(i.rd,r(i.rs1)^r(i.rs2))
        elif op==Op.NOT: w(i.rd,~r(i.rs1))
        elif op==Op.SHL: w(i.rd,r(i.rs1)<<(r(i.rs2)&8191))
        elif op==Op.SHR: w(i.rd,r(i.rs1)>>(r(i.rs2)&8191))
        elif op==Op.SAR: w(i.rd,s8192(r(i.rs1))>>(r(i.rs2)&8191))
        elif op==Op.CMP:
            z=u8192(r(i.rs1)-r(i.rs2)); self.flags.z=(z==0); self.flags.n=bool(z>>8191); self.flags.c=r(i.rs1)<r(i.rs2)
        elif op==Op.CMPI:
            z=u8192(r(i.rs1)-i.imm); self.flags.z=(z==0); self.flags.n=bool(z>>8191); self.flags.c=r(i.rs1)<i.imm
        elif op in (Op.LOAD,Op.LDX):
            a=(r(i.rs1)+i.imm)&ADDR_MASK; n=i.size or WORD_BYTES; w(i.rd,int.from_bytes(self.memory.read(a,n),"little"))
        elif op in (Op.STORE,Op.STX):
            a=(r(i.rs1)+i.imm)&ADDR_MASK; n=i.size or WORD_BYTES; self.memory.write(a,r(i.rs2).to_bytes(n,"little"))
        elif op==Op.BEQ and r(i.rs1)==r(i.rs2): nxt=(self.pc+i.imm)&ADDR_MASK
        elif op==Op.BNE and r(i.rs1)!=r(i.rs2): nxt=(self.pc+i.imm)&ADDR_MASK
        elif op==Op.BLT and s8192(r(i.rs1))<s8192(r(i.rs2)): nxt=(self.pc+i.imm)&ADDR_MASK
        elif op==Op.BGT and s8192(r(i.rs1))>s8192(r(i.rs2)): nxt=(self.pc+i.imm)&ADDR_MASK
        elif op==Op.JMP: nxt=(self.pc+i.imm)&ADDR_MASK
        elif op==Op.CALL: self.lr=nxt; w(31,nxt); nxt=(self.pc+i.imm)&ADDR_MASK
        elif op==Op.RET: nxt=r(31)
        elif op==Op.PUSH: self.sp-=WORD_BYTES; self.putword(self.sp,r(i.rs1))
        elif op==Op.POP: w(i.rs1,self.word(self.sp)); self.sp+=WORD_BYTES
        elif op==Op.CAS:
            a=r(i.rd); oldv=self.word(a); w(i.rd,oldv)
            if oldv==r(i.rs1): self.putword(a,r(i.rs2))
        elif op in (Op.FENCE,Op.FLUSH): self.memory.cache.flush()
        elif op==Op.INVL: self.memory.cache.invalidate()
        elif op in (Op.VADD,Op.VMUL,Op.VXOR):
            a,b=self.V[i.rs1],self.V[i.rs2]
            if op==Op.VADD: self.V[i.rd]=[u8192(x+y) for x,y in zip(a,b)]
            elif op==Op.VMUL: self.V[i.rd]=[u8192(x*y) for x,y in zip(a,b)]
            else: self.V[i.rd]=[x^y for x,y in zip(a,b)]
        elif op==Op.VDOT: self.V[i.rd][0]=u8192(sum(x*y for x,y in zip(self.V[i.rs1],self.V[i.rs2])))
        elif op in (Op.VLOAD,Op.VSTORE):
            a=(r(i.rs1)+i.imm)&ADDR_MASK; n=i.size or WORD_BYTES
            if op==Op.VLOAD:
                d=self.memory.read(a,n); m=min(128,len(d)//8); self.V[i.rd][:m]=struct.unpack("<"+"Q"*m,d[:8*m])
            else:
                d=struct.pack("<"+"Q"*128,*self.V[i.rs2]); self.memory.write(a,d[:n])
        elif op==Op.DMA_COPY:
            so=i.imm&0xffffffff; do=(i.imm>>32)&0xffffffff
            self.memory.raw((r(i.rs2)+do)&ADDR_MASK,self.memory.raw((r(i.rs1)+so)&ADDR_MASK,i.size)); self.memory.cache.invalidate()
        elif op==Op.NET_TX: self.tx.push(Desc((r(i.rs1)+i.imm)&ADDR_MASK,i.size))
        elif op==Op.NET_RX:
            d=self.rx.pop()
            if d: w(i.rs1,d.address); w(1,d.length)
        elif op==Op.SYS:
            if i.imm==1: self.memory.write(UART_TX,bytes([r(1)&255]))
            elif i.imm==2: self.memory.cache.flush()
            elif i.imm==3: self.halted=True
        else: raise NotImplementedError(op)
        self.pc=nxt; self.cycles+=1; self.instructions+=1; return i
    def run(self,limit=1_000_000):
        n=0
        while not self.halted and n<limit: self.step(); n+=1
        return n

def disasm(data,mode="risc"):
    p=0; pc=0; out=[]
    while p<len(data):
        if mode=="risc":
            if p+RISC_BYTES>len(data): break
            i=RISC.dec(data[p:p+RISC_BYTES]); n=RISC_BYTES
        else: i,n=CISC.dec(data[p:])
        out.append(f"{pc:016x}: {i.op.name:8s} rd={i.rd} rs1={i.rs1} rs2={i.rs2} imm={i.imm}"); p+=n; pc+=n
    return out

def selftest():
    source="""
        MOVI R1, 5
        MOVI R2, 7
        ADD R3, R1, R2
        MOVI R4, 4096
        STORE R3, [R4]
        LOAD R5, [R4]
        HALT
    """
    for mode in ("risc","cisc"):
        image,_=Assembler(mode).assemble(source); c=CPU(mode,2*1024*1024); c.load(image); c.run(100); assert c.r(3)==12 and c.r(5)==12
    t=TensorBackend("auto"); assert t.add8192((1<<8191)-1,1)==(1<<8191)
    print("SELF-TEST: PASS")

if __name__=="__main__":
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True)
    sp.add_parser("selftest"); x=ap.parse_args()
    if x.cmd=="selftest": selftest()
