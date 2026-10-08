#!/usr/bin/env python3
"""RV32I machine model for Chimera: 32-bit memory, traps, and a documented subset.

Implements the RV32I integer/control/load-store/fence/system instruction base used
by this simulator, with a minimal M-mode trap model. Not a privileged-spec-complete
SoC: CSRs/interrupt delivery/PMP/MMU/device buses are intentionally not claimed.
"""
from dataclasses import dataclass, field

MASK = 0xffffffff
class Trap(Exception):
    def __init__(self, cause, pc, tval=0, message="trap"):
        super().__init__(message); self.cause=cause; self.pc=pc & MASK; self.tval=tval & MASK

@dataclass
class RV32Machine:
    memory_size: int = 65536
    base: int = 0
    regs: list = field(default_factory=lambda:[0]*32)
    pc: int = 0
    memory: bytearray = field(default_factory=bytearray)
    mtvec: int = 0
    mcause: int = 0
    mepc: int = 0
    mtval: int = 0
    privilege: str = "M"
    halted: bool = False
    steps: int = 0

    def __post_init__(self):
        if not self.memory: self.memory=bytearray(self.memory_size)
        if len(self.regs)!=32: raise ValueError("RV32 requires 32 integer registers")
    def load(self, address, data):
        off=address-self.base
        if off<0 or off+len(data)>len(self.memory): raise Trap(7,self.pc,address,"store access fault")
        self.memory[off:off+len(data)]=data
    def read(self,address,size,signed_load=False):
        off=address-self.base
        if off<0 or off+size>len(self.memory): raise Trap(5,self.pc,address,"load access fault")
        if address%size: raise Trap(4,self.pc,address,"load address misaligned")
        v=int.from_bytes(self.memory[off:off+size],"little")
        if signed_load and v&(1<<(size*8-1)): v-=1<<(size*8)
        return v&MASK
    def write(self,address,size,value):
        off=address-self.base
        if off<0 or off+size>len(self.memory): raise Trap(7,self.pc,address,"store access fault")
        if address%size: raise Trap(6,self.pc,address,"store address misaligned")
        self.memory[off:off+size]=(value&MASK).to_bytes(4,"little")[:size]
    @staticmethod
    def sx(v,bits):
        v &= (1<<bits)-1
        return v-(1<<bits) if v&(1<<(bits-1)) else v
    def trap(self,cause,pc,tval=0):
        self.mcause=cause; self.mepc=pc&MASK; self.mtval=tval&MASK
        if self.mtvec: self.pc=self.mtvec & ~3
        else: self.halted=True
    def step(self):
        if self.halted: return
        here=self.pc
        try:
            if here%4: raise Trap(0,here,here,"instruction address misaligned")
            w=self.read(here,4)
            op=w&0x7f; rd=(w>>7)&31; f3=(w>>12)&7; a=(w>>15)&31; b=(w>>20)&31; f7=w>>25
            imm_i=self.sx(w>>20,12)
            imm_s=self.sx(((w>>25)<<5)|((w>>7)&31),12)
            imm_b=self.sx((((w>>31)&1)<<12)|(((w>>7)&1)<<11)|(((w>>25)&63)<<5)|(((w>>8)&15)<<1),13)
            imm_j=self.sx((((w>>31)&1)<<20)|(((w>>12)&255)<<12)|(((w>>20)&1)<<11)|(((w>>21)&1023)<<1),21)
            x,y=self.regs[a],self.regs[b]; nxt=(here+4)&MASK; val=None
            if op==0x37: val=w&0xfffff000
            elif op==0x17: val=(here+(w&0xfffff000))&MASK
            elif op==0x6f: val=nxt; nxt=(here+imm_j)&MASK
            elif op==0x67 and f3==0:
                target=(x+imm_i)&MASK
                if target&3: raise Trap(0,here,target,"JALR target misaligned")
                val=nxt; nxt=target
            elif op==0x63:
                cond={0:x==y,1:x!=y,4:self.sx(x,32)<self.sx(y,32),5:self.sx(x,32)>=self.sx(y,32),6:x<y,7:x>=y}.get(f3)
                if cond is None: raise Trap(2,here,w,"illegal branch funct3")
                if cond:
                    nxt=(here+imm_b)&MASK
                    if nxt&3: raise Trap(0,here,nxt,"branch target misaligned")
            elif op==0x03:
                spec={0:(1,True),1:(2,True),2:(4,False),4:(1,False),5:(2,False)}.get(f3)
                if spec is None: raise Trap(2,here,w,"illegal load funct3")
                size,sgn=spec; val=self.read((x+imm_i)&MASK,size,sgn)
            elif op==0x23:
                size={0:1,1:2,2:4}.get(f3)
                if size is None: raise Trap(2,here,w,"illegal store funct3")
                self.write((x+imm_s)&MASK,size,y)
            elif op==0x13:
                sh=(w>>20)&31
                if f3==0: val=x+imm_i
                elif f3==2: val=int(self.sx(x,32)<imm_i)
                elif f3==3: val=int(x<(imm_i&MASK))
                elif f3==4: val=x^(imm_i&MASK)
                elif f3==6: val=x | (imm_i&MASK)
                elif f3==7: val=x & (imm_i&MASK)
                elif f3==1 and (w>>25)==0: val=x<<sh
                elif f3==5 and (w>>25)==0: val=x>>sh
                elif f3==5 and (w>>25)==0x20: val=self.sx(x,32)>>sh
                else: raise Trap(2,here,w,"illegal OP-IMM encoding")
            elif op==0x33:
                table={(0,0):lambda:x+y,(0x20,0):lambda:x-y,(0,1):lambda:x<<(y&31),(0,2):lambda:int(self.sx(x,32)<self.sx(y,32)),(0,3):lambda:int(x<y),(0,4):lambda:x^y,(0,5):lambda:x>>(y&31),(0x20,5):lambda:self.sx(x,32)>>(y&31),(0,6):lambda:x|y,(0,7):lambda:x&y}
                fn=table.get((f7,f3))
                if fn is None: raise Trap(2,here,w,"illegal OP encoding")
                val=fn()
            elif op==0x0f: # RV32I FENCE; single-hart execution preserves program order.
                # FENCE.I belongs to Zifencei, not the RV32I base.
                fm=(w>>28)&0xf; pred=(w>>24)&0xf; succ=(w>>20)&0xf
                if f3 != 0 or rd or a or fm != 0:
                    raise Trap(2,here,w,"illegal FENCE encoding")
                # There are no asynchronous memory observers in this model, so
                # sequential execution is already stronger than the requested ordering.
            elif op==0x73:
                if w==0x00000073: raise Trap(8 if self.privilege=="U" else 11,here,0,"ECALL")
                if w==0x00100073: raise Trap(3,here,here,"EBREAK")
                if w==0x30200073 and self.privilege=="M":
                    nxt=self.mepc
                else: raise Trap(2,here,w,"unsupported or illegal SYSTEM/CSR instruction")
            else: raise Trap(2,here,w,"illegal instruction")
            if val is not None and rd: self.regs[rd]=val&MASK
            self.pc=nxt; self.regs[0]=0; self.steps+=1
        except Trap as t:
            self.trap(t.cause,t.pc,t.tval)
    def run(self,max_steps=100000):
        start=self.steps
        while not self.halted and self.steps-start<max_steps: self.step()
        return {"pc":self.pc,"steps":self.steps-start,"halted":self.halted,"registers":self.regs[:],
                "mcause":self.mcause,"mepc":self.mepc,"mtval":self.mtval,"privilege":self.privilege}
