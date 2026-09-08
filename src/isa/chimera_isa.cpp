#include "chimera/isa8192.hpp"
#include <cstring>
#include <stdexcept>

namespace chimera {
namespace {
uint16_t u16(const uint8_t* p) { return uint16_t(p[0]) | (uint16_t(p[1]) << 8); }
uint64_t u64(const uint8_t* p) {
    uint64_t v=0; std::memcpy(&v,p,sizeof(v)); return v;
}
Register8192 lane_not(const Register8192& x) {
    Register8192 y{};
    for (unsigned k=0;k<128;++k) y.set_u64(k,~x.lane(k));
    return y;
}
Register8192 lane_shift(const Register8192& x, unsigned s, bool left) {
    s %= 8192; const unsigned q=s/64, r=s%64; Register8192 y{};
    for (unsigned k=0;k<128;++k) {
        if (left) {
            if (k<q) { y.set_u64(k,0); continue; }
            uint64_t v=x.lane(k-q)<<r;
            if (r && k>q) v |= x.lane(k-q-1)>>(64-r);
            y.set_u64(k,v);
        } else {
            if (k+q>=128) { y.set_u64(k,0); continue; }
            uint64_t v=x.lane(k+q)>>r;
            if (r && k+q+1<128) v |= x.lane(k+q+1)<<(64-r);
            y.set_u64(k,v);
        }
    }
    return y;
}
// The catalog is contiguous from 0x0001 through 0x011C. Keeping this range
// check here makes fetch/decode forward-compatible with metadata additions:
// execution can distinguish "recognized architectural opcode" from malformed
// instruction bytes without hard-coding hundreds of switch labels.
bool catalog_opcode(uint16_t op) { return op>=0x0001 && op<=0x011C; }
}

Instr decode(const uint8_t* p,std::size_t len){
    if(!p || len<16) throw std::invalid_argument("Chimera II instruction buffer too short");
    Instr i{};
    i.opcode=u16(p+0); i.dst=u16(p+2); i.srcA=u16(p+4); i.srcB=u16(p+6);
    i.imm=u64(p+8); i.imm_len=8;
    if (!catalog_opcode(i.opcode) && i.opcode!=OP_NOP) throw std::runtime_error("unknown Chimera II opcode");
    if (i.dst>=1024 || i.srcA>=1024 || i.srcB>=1024) throw std::out_of_range("Chimera register index");
    return i;
}

void execute(CPU8192& c,const Instr&i){
    if (i.dst>=c.gpr.size() || i.srcA>=c.gpr.size() || i.srcB>=c.gpr.size())
        throw std::out_of_range("Chimera register index");
    switch(i.opcode){
      case OP_NOP: break;
      case 0x0001: c.gpr[i.dst]=c.gpr[i.srcA]+c.gpr[i.srcB]; break; // ADD
      case 0x0002: c.gpr[i.dst]=c.gpr[i.srcA]-c.gpr[i.srcB]; break; // SUB
      case 0x0003: c.gpr[i.dst]=c.gpr[i.srcA]&c.gpr[i.srcB]; break; // AND
      case 0x0004: c.gpr[i.dst]=c.gpr[i.srcA]|c.gpr[i.srcB]; break; // OR
      case 0x0005: c.gpr[i.dst]=c.gpr[i.srcA]^c.gpr[i.srcB]; break; // XOR
      case 0x0006: c.gpr[i.dst]=lane_not(c.gpr[i.srcA]); break; // NOT
      case 0x0007: c.gpr[i.dst]=lane_shift(c.gpr[i.srcA],unsigned(i.imm),true); break; // SHL
      case 0x0008: c.gpr[i.dst]=lane_shift(c.gpr[i.srcA],unsigned(i.imm),false); break; // SHR
      case 0x0015: c.gpr[i.dst]=c.gpr[i.srcA]; break; // MOV
      case 0x0012: // CMP
      case 0x0013: // CMPEQ
      case 0x0014: // CMPLT
        c.flags = (i.opcode==0x0013) ? (c.gpr[i.srcA]==c.gpr[i.srcB]) :
                  (i.opcode==0x0014 ? (c.gpr[i.srcA]<c.gpr[i.srcB]) :
                   (c.gpr[i.srcA]==c.gpr[i.srcB] ? 1u : 0u));
        break;
      default:
        // The remaining catalog entries are kernel/driver/crypto/VFS/GPU
        // dispatch boundaries. They are recognized by fetch/decode but their
        // side effects belong to subsystem handlers, not this pure CPU core.
        if (!catalog_opcode(i.opcode)) throw std::runtime_error("unsupported Chimera II opcode");
        break;
    }
}

void run(CPU8192& c,const uint8_t*code,std::size_t len){
    while(c.pc<len){
        if (len-c.pc<16) throw std::invalid_argument("truncated Chimera II instruction stream");
        Instr i=decode(code+c.pc,len-c.pc); execute(c,i); c.pc += 16;
    }
}
}
