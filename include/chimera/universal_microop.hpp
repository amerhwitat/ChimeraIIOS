#pragma once
#include <array>
#include <cstdint>
#include <string_view>

namespace chimera::universal_isa {

// Canonical semantic operations. Foreign instructions are decoded by an
// architecture backend and lowered to these operations before execution.
enum class MicroOp : std::uint16_t {
    Nop = 0x0000,
    Move,
    Add,
    Sub,
    Mul,
    Div,
    Mod,
    And,
    Or,
    Xor,
    Not,
    Shift,
    Rotate,
    Compare,
    Branch,
    Call,
    Return,
    Load,
    Store,
    Atomic,
    Fence,
    Vector,
    Matrix,
    TensorContract,
    Crypto,
    Syscall,
    Trap,
    Privileged,
    NetSend,
    NetReceive,
    IoRead,
    IoWrite,
};

struct MicroOpRecord {
    MicroOp op;
    std::uint16_t dst;
    std::uint16_t src_a;
    std::uint16_t src_b;
    std::uint64_t immediate;
    std::uint32_t flags;
};

struct LoweringContract {
    std::string_view target;
    std::string_view source_mnemonic;
    MicroOp op;
    bool privileged;
    bool may_trap;
    bool memory_access;
};

inline constexpr LoweringContract kCoreContracts[] = {
    {"generic", "MOV", MicroOp::Move, false, false, false},
    {"generic", "ADD", MicroOp::Add, false, false, false},
    {"generic", "SUB", MicroOp::Sub, false, false, false},
    {"generic", "MUL", MicroOp::Mul, false, false, false},
    {"generic", "DIV", MicroOp::Div, false, true, false},
    {"generic", "LOAD", MicroOp::Load, false, true, true},
    {"generic", "STORE", MicroOp::Store, false, true, true},
    {"generic", "ATOMIC", MicroOp::Atomic, false, true, true},
    {"generic", "FENCE", MicroOp::Fence, false, false, true},
    {"generic", "BRANCH", MicroOp::Branch, false, true, false},
    {"generic", "SYSCALL", MicroOp::Syscall, true, true, false},
    {"generic", "TRAP", MicroOp::Trap, true, true, false},
    {"generic", "TCONTRACT", MicroOp::TensorContract, false, true, false},
    {"generic", "NETSEND", MicroOp::NetSend, false, true, true},
};

constexpr std::size_t contract_count() noexcept {
    return sizeof(kCoreContracts) / sizeof(kCoreContracts[0]);
}

constexpr std::array<std::uint8_t, 16> canonical_record_bytes(const MicroOpRecord& r) noexcept {
    std::array<std::uint8_t, 16> b{};
    b[0] = static_cast<std::uint8_t>(static_cast<std::uint16_t>(r.op));
    b[1] = static_cast<std::uint8_t>(static_cast<std::uint16_t>(r.op) >> 8);
    b[2] = static_cast<std::uint8_t>(r.dst);
    b[3] = static_cast<std::uint8_t>(r.dst >> 8);
    b[4] = static_cast<std::uint8_t>(r.src_a);
    b[5] = static_cast<std::uint8_t>(r.src_a >> 8);
    b[6] = static_cast<std::uint8_t>(r.src_b);
    b[7] = static_cast<std::uint8_t>(r.src_b >> 8);
    for (unsigned i = 0; i < 8; ++i) b[8 + i] = static_cast<std::uint8_t>(r.immediate >> (i * 8));
    return b;
}

} // namespace chimera::universal_isa
