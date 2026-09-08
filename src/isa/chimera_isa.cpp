#include "chimera/isa8192.hpp"
#include <cstring>
#include <stdexcept>
namespace chimera {
Instr decode(const uint8_t* p,std::size_t len){
    if(!p||len<8) throw std::invalid_argument("instruction buffer too short");
    Instr i{}; i.opcode=p[0]; i.dst=p[1]|(uint16_t(p[2])<<8); i.srcA=p[3]|(uint16_t(p[4])<<8); i.srcB=p[5]|(uint16_t(p[6])<<8); i.imm=p[7]; i.imm_len=1; return i;
}
void execute(CPU8192& c,const Instr&i){
    switch(i.opcode){
      case OP_NOP: break;
      case OP_ADD: c.gpr[i.dst]=c.gpr[i.srcA]+c.gpr[i.srcB]; break;
      case OP_XOR: c.gpr[i.dst]=c.gpr[i.srcA]^c.gpr[i.srcB]; break;
      case OP_SHL: { auto x=c.gpr[i.srcA]; const unsigned s=i.imm%8192; const unsigned q=s/64,r=s%64; Register8192 y{}; for(unsigned k=0;k<128;++k){ if(k<q) y.set_u64(k,0); else { uint64_t v=x.lane(k-q)<<r; if(r&&k>q) v|=x.lane(k-q-1)>>(64-r); y.set_u64(k,v); } } c.gpr[i.dst]=y; break; }
      default: throw std::runtime_error("unsupported Chimera opcode");
    }
}
void run(CPU8192& c,const uint8_t*code,std::size_t len){ while(c.pc<len){ Instr i=decode(code+c.pc,len-c.pc); execute(c,i); c.pc += 8 + i.imm_len; } }
}
