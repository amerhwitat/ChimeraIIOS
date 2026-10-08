#!/usr/bin/env python3
"""Reference interpreter for the experimental Chimera N-bit ISA v0.1.

This is a deterministic reference model, not a production hypervisor. N is
selectable (32/64/128-bit GPRs); instruction words are fixed 32-bit little-endian.
"""
from dataclasses import dataclass, field

MASK32 = 0xffffffff
REGS = 16
# Encoding: [31:24 opcode][23:20 rd][19:16 ra][15:12 rb][11:0 signed immediate]
OP_NOP=0x00; OP_LI=0x01; OP_ADD=0x02; OP_SUB=0x03; OP_AND=0x04
OP_OR=0x05; OP_XOR=0x06; OP_LOAD=0x10; OP_STORE=0x11
OP_JMP=0x20; OP_JZ=0x21; OP_TRAP=0x30; OP_HALT=0xff

class NBitTrap(Exception):
    def __init__(self,cause,pc,detail=""):
        super().__init__(detail or cause); self.cause=cause; self.pc=pc

@dataclass
class ChimeraNBit:
    nbits:int=32
    memory_size:int=65536
    pc:int=0
    regs:list=field(default_factory=lambda:[0]*REGS)
    memory:bytearray=field(default_factory=bytearray)
    halted:bool=False
    steps:int=0
    trap_vector:int=0x100
    trap_cause:str|None=None
    device_log:list=field(default_factory=list)

    def __post_init__(self):
        if self.nbits not in (32,64,128): raise ValueError("N must be 32, 64, or 128")
        if self.memory_size<4096 or self.memory_size%4: raise ValueError("memory size must be >=4096 and 4-byte aligned")
        if not self.memory: self.memory=bytearray(self.memory_size)
        if len(self.memory)!=self.memory_size: raise ValueError("memory length mismatch")
        if len(self.regs)!=REGS: raise ValueError("exactly 16 registers required")
        self.mask=(1<<self.nbits)-1

    @staticmethod
    def encode(op,rd=0,ra=0,rb=0,imm=0):
        if not (0<=op<=255 and 0<=rd<16 and 0<=ra<16 and 0<=rb<16 and -2048<=imm<=2047):
            raise ValueError("instruction field out of range")
        return (op<<24)|(rd<<20)|(ra<<16)|(rb<<12)|(imm&0xfff)

    def load_program(self,words,address=0):
        if address<0 or address%4 or address+4*len(words)>self.memory_size:
            raise NBitTrap("instruction-access",address)
        for i,w in enumerate(words): self.memory[address+4*i:address+4*i+4]=int(w).to_bytes(4,"little")

    def _read(self,address,size):
        if address<0 or address+size>self.memory_size: raise NBitTrap("load-access",self.pc,f"address {address}")
        return int.from_bytes(self.memory[address:address+size],"little")

    def _write(self,address,size,value):
        if address<0 or address+size>self.memory_size: raise NBitTrap("store-access",self.pc,f"address {address}")
        self.memory[address:address+size]=(value&((1<<(size*8))-1)).to_bytes(size,"little")

    def step(self):
        if self.halted: return
        oldpc=self.pc
        if self.pc%4: raise NBitTrap("instruction-misaligned",self.pc)
        word=self._read(self.pc,4); self.pc+=4
        op=(word>>24)&255; rd=(word>>20)&15; ra=(word>>16)&15; rb=(word>>12)&15
        imm=word&0xfff; imm=imm-4096 if imm&0x800 else imm
        a=self.regs[ra]; b=self.regs[rb]
        if op==OP_NOP: pass
        elif op==OP_LI: self.regs[rd]=imm&self.mask
        elif op==OP_ADD: self.regs[rd]=(a+b)&self.mask
        elif op==OP_SUB: self.regs[rd]=(a-b)&self.mask
        elif op==OP_AND: self.regs[rd]=a&b
        elif op==OP_OR: self.regs[rd]=a|b
        elif op==OP_XOR: self.regs[rd]=a^b
        elif op==OP_LOAD: self.regs[rd]=self._read((a+imm)&self.mask,self.nbits//8)
        elif op==OP_STORE: self._write((a+imm)&self.mask,self.nbits//8,b)
        elif op==OP_JMP: self.pc=(oldpc+imm*4)&self.mask
        elif op==OP_JZ:
            if a==0:self.pc=(oldpc+imm*4)&self.mask
        elif op==OP_TRAP:
            self.trap_cause=f"software:{imm&0xfff}"; self.device_log.append({"device":"trap","cause":self.trap_cause,"pc":oldpc})
            self.pc=self.trap_vector
        elif op==OP_HALT:self.halted=True
        else: raise NBitTrap("illegal-instruction",oldpc,f"opcode 0x{op:02x}")
        self.regs[0]=0
        self.steps+=1

    def run(self,max_steps=100000):
        if max_steps<1: raise ValueError("max_steps must be positive")
        while not self.halted and self.steps<max_steps:
            try:self.step()
            except NBitTrap as t:
                self.trap_cause=t.cause; self.device_log.append({"device":"trap","cause":t.cause,"pc":t.pc,"detail":str(t)})
                raise
        return {"halted":self.halted,"steps":self.steps,"pc":self.pc,"nbits":self.nbits,"registers":list(self.regs),"trap_cause":self.trap_cause,"devices":list(self.device_log)}

if __name__=="__main__":
    import json
    cpu=ChimeraNBit()
    cpu.load_program([cpu.encode(OP_LI,1,imm=7),cpu.encode(OP_LI,2,imm=9),cpu.encode(OP_ADD,3,1,2),cpu.encode(OP_HALT)])
    print(json.dumps(cpu.run(),indent=2))
