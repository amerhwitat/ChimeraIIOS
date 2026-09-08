#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include "chimera/RegisterN.hpp"

namespace chimera {
struct Instr { uint8_t opcode=0; uint16_t dst=0, srcA=0, srcB=0; uint64_t imm=0; uint8_t imm_len=0; };
struct CPU8192 { std::array<Register8192,1024> gpr{}; uint64_t pc=0; uint64_t flags=0; };

constexpr uint8_t OP_NOP=0x00, OP_ADD=0x01, OP_XOR=0x02, OP_SHL=0x03, OP_CHKSUM8192=0x52;
Instr decode(const uint8_t* p, std::size_t len=16);
void execute(CPU8192&, const Instr&);
void run(CPU8192&, const uint8_t*, std::size_t);
}
