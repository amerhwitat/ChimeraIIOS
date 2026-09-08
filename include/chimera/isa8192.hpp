#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>
#include "chimera/RegisterN.hpp"

namespace chimera {

// Canonical Chimera-II native fetch packet:
// [15:0] opcode (little-endian), [31:16] rd, [47:32] srcA,
// [63:48] srcB, followed by an optional 64-bit immediate.
struct Instr {
    std::uint16_t opcode=0;
    std::uint16_t dst=0, srcA=0, srcB=0;
    std::uint64_t imm=0;
    std::uint8_t imm_len=0;
    std::uint8_t length=8;
};

struct CPU8192 {
    std::array<Register8192,1024> gpr{};
    std::uint64_t pc=0;
    std::uint64_t flags=0;
};

struct OpcodeInfo {
    std::uint16_t opcode;
    std::string_view mnemonic;
    std::string_view encoding;
    std::string_view operands;
    bool privileged;
    std::uint16_t latency;
    double throughput;
    std::string_view pipeline_stage;
    std::string_view isa_family;
    std::string_view notes;
    std::string_view source_ref;
};

enum class ExecuteStatus : std::uint8_t {
    Executed,
    PrivilegeViolation,
    InvalidOpcode,
    UnimplementedService
};

constexpr std::uint16_t OP_ADD=0x0001, OP_SUB=0x0002, OP_AND=0x0003, OP_OR=0x0004,
    OP_XOR=0x0005, OP_NOT=0x0006, OP_SHL=0x0007, OP_SHR=0x0008,
    OP_ROL=0x0009, OP_ROR=0x000A, OP_MUL=0x000B, OP_MULHI=0x000C,
    OP_MULMOD=0x000D, OP_MODEXP=0x000E, OP_BARRETT=0x000F, OP_DIV=0x0010,
    OP_REM=0x0011, OP_CMP=0x0012, OP_CMPEQ=0x0013, OP_CMPLT=0x0014,
    OP_MOV=0x0015, OP_LOAD=0x0016, OP_STORE=0x0017, OP_PREFETCH=0x0018,
    OP_MEMCPY=0x0019, OP_MEMSET=0x001A, OP_TRAP=0x0046, OP_SYS_CALL=0x0047,
    OP_SVC=0x0048, OP_FENCE=0x00D3, OP_BARRIER=0x00D4;

constexpr std::uint16_t OP_NOP=0x0000;
constexpr std::uint16_t OP_CHKSUM8192=0x0052;

Instr decode(const std::uint8_t* p, std::size_t len=16);
ExecuteStatus execute(CPU8192&, const Instr&, bool privileged=false);
void run(CPU8192&, const std::uint8_t*, std::size_t, bool privileged=false);

bool is_defined_opcode(std::uint16_t opcode) noexcept;
const OpcodeInfo* opcode_info(std::uint16_t opcode) noexcept;
std::string_view opcode_name(std::uint16_t opcode) noexcept;

} // namespace chimera
