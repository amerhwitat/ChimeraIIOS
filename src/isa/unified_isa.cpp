#include "chimera/unified_isa.hpp"
#include <cstddef>

namespace chimera::isa {
static int32_t sext(uint32_t x, unsigned bits) { const uint32_t m=1u<<(bits-1); return static_cast<int32_t>((x^m)-m); }

DecoderResult decode_riscv32(uint32_t w) {
    Instruction i; i.family=Family::RV32I; i.raw=w; i.length=4; i.opcode=w&0x7f; i.rd=(w>>7)&31; i.rs1=(w>>15)&31; i.rs2=(w>>20)&31;
    switch(i.opcode) {
        case 0x33: i.kind=Kind::Integer; i.mnemonic=((w>>12)&7)==0 ? ((w>>30)&1?"sub":"add") : ((w>>12)&7)==4?"xor":"integer"; break;
        case 0x13: i.kind=Kind::Integer; i.immediate=sext(w>>20,12); i.mnemonic="op-imm"; break;
        case 0x03: i.kind=Kind::LoadStore; i.immediate=sext(w>>20,12); i.mnemonic="load"; break;
        case 0x23: i.kind=Kind::LoadStore; i.immediate=sext(((w>>25)<<5)|((w>>7)&31),12); i.mnemonic="store"; break;
        case 0x63: i.kind=Kind::Branch; i.mnemonic="branch"; break;
        case 0x6f: i.kind=Kind::Branch; i.mnemonic="jal"; break;
        case 0x67: i.kind=Kind::Branch; i.mnemonic="jalr"; break;
        case 0x37: i.kind=Kind::Integer; i.mnemonic="lui"; break;
        case 0x17: i.kind=Kind::Integer; i.mnemonic="auipc"; break;
        case 0x73: i.kind=Kind::System; i.mnemonic=((w>>20)==0)?"ecall":"system"; break;
        case 0x2f: i.kind=Kind::Atomic; i.mnemonic="atomic"; break;
        default: return {i,false};
    }
    return {i,true};
}
DecoderResult decode_riscv64(uint32_t w) { auto r=decode_riscv32(w); r.instruction.family=Family::RV64I; return r; }
DecoderResult decode_aarch64(uint32_t w) {
    Instruction i; i.family=Family::AArch64; i.raw=w; i.length=4; i.rd=w&31; i.rs1=(w>>5)&31; i.rs2=(w>>16)&31;
    // Major architectural classes; exact encodings are intentionally decoded only where stable here.
    if((w&0x7f000000u)==0x11000000u) { i.kind=Kind::Integer; i.mnemonic="add/sub-immediate"; return {i,true}; }
    if((w&0x3b000000u)==0x18000000u) { i.kind=Kind::LoadStore; i.mnemonic="load-literal"; return {i,true}; }
    if((w&0x7c000000u)==0x14000000u) { i.kind=Kind::Branch; i.mnemonic="branch"; return {i,true}; }
    if((w&0xff000000u)==0xd4000000u) { i.kind=Kind::System; i.mnemonic="system"; return {i,true}; }
    return {i,false};
}
DecoderResult decode_x86_64(const uint8_t* b, std::size_t n) {
    Instruction i; i.family=Family::X86_64; if(!b||!n) return {i,false}; i.raw=b[0]; i.length=1;
    switch(b[0]) { case 0x90:i.kind=Kind::Control;i.mnemonic="nop";break; case 0xc3:i.kind=Kind::Control;i.mnemonic="ret";break; case 0xe8:i.kind=Kind::Branch;i.mnemonic="call-rel";break; case 0xe9:i.kind=Kind::Branch;i.mnemonic="jmp-rel";break; case 0xeb:i.kind=Kind::Branch;i.mnemonic="jmp-short";break; case 0x05:i.kind=Kind::Integer;i.mnemonic="add-eax-imm32";break; case 0x31:i.kind=Kind::Integer;i.mnemonic="xor-r/m32-r32";break; case 0x89:i.kind=Kind::Integer;i.mnemonic="mov-r/m-r";break; case 0x8b:i.kind=Kind::LoadStore;i.mnemonic="mov-r-r/m";break; case 0x0f: if(n>1&&b[1]==0x05){i.length=2;i.kind=Kind::System;i.mnemonic="syscall";break;} return {i,false}; default:return {i,false}; }
    return {i,true};
}
std::string_view family_name(Family f){switch(f){case Family::Chimera8192:return "Chimera-8192";case Family::RV32I:return "RV32I";case Family::RV64I:return "RV64I";case Family::AArch64:return "AArch64";case Family::X86_64:return "x86-64";}return "unknown";}
std::string_view kind_name(Kind k){switch(k){case Kind::Integer:return "integer";case Kind::LoadStore:return "load/store";case Kind::Branch:return "branch";case Kind::System:return "system";case Kind::Atomic:return "atomic";case Kind::Vector:return "vector";case Kind::Floating:return "floating";case Kind::Crypto:return "crypto";case Kind::Control:return "control";default:return "invalid";}}
FeatureSet features(Family f){FeatureSet x; switch(f){case Family::RV32I: x.privileged=true; break; case Family::RV64I:x.privileged=true;x.atomics=true;x.floating=true;x.vector=true;x.crypto=true;break;case Family::AArch64:x.privileged=true;x.floating=true;x.vector=true;x.crypto=true;break;case Family::X86_64:x.privileged=true;x.floating=true;x.vector=true;x.crypto=true;x.variable_length=true;break;case Family::Chimera8192:x.atomics=true;x.vector=true;x.crypto=true;x.tensor=true;x.privileged=true;x.variable_length=true;break;} return x;}
}
