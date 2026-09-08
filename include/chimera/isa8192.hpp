#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include "chimera/RegisterN.hpp"

namespace chimera {
// Canonical Chimera II instruction container. The opcode field is 16-bit because
// the unified ISA catalog occupies 0x0001..0x011C. The legacy register fields
// remain 16-bit and the immediate remains 64-bit for host emulation.
struct Instr {
    uint16_t opcode=0;
    uint16_t dst=0, srcA=0, srcB=0;
    uint64_t imm=0;
    uint8_t imm_len=0;
};
struct CPU8192 { std::array<Register8192,1024> gpr{}; uint64_t pc=0; uint64_t flags=0; };

constexpr uint16_t OP_NOP=0x0000;
constexpr uint16_t OP_ADD=0x0001;
constexpr uint16_t OP_XOR=0x0005;
constexpr uint16_t OP_SHL=0x0007;
constexpr uint16_t OP_CHKSUM8192=0x0052;

// Canonical fixed-width host-emulation encoding: opcode(16), rd(16), rs(16),
// rt(16), immediate(64). This is deliberately separate from the semantic
// encoding column in tools/isa/chimera_isa_r8192_complete.csv.
Instr decode(const uint8_t* p, std::size_t len=16);
void execute(CPU8192&, const Instr&);
void run(CPU8192&, const uint8_t*, std::size_t);
}
