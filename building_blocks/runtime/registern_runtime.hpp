#pragma once
#include <array>
#include <cstdint>

namespace chimera::runtime {

template <std::size_t Bits>
struct WideRegister {
    static_assert(Bits % 64 == 0);
    std::array<std::uint64_t, Bits / 64> limbs{};
    constexpr void clear() noexcept { limbs.fill(0); }
    constexpr std::uint64_t low() const noexcept { return limbs[0]; }
};

enum class MicroOp : std::uint16_t {
    Nop, Add, Sub, Mul, Div, Load, Store, And, Or, Xor,
    ShiftLeft, ShiftRight, Branch, Call, Return,
    Fence, AtomicCas, NetSend, NetReceive, TensorContract
};

struct DecodedInstruction {
    MicroOp op{MicroOp::Nop};
    std::uint16_t rd{};
    std::uint16_t rs1{};
    std::uint16_t rs2{};
    std::int32_t immediate{};
};

} // namespace chimera::runtime
