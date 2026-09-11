#pragma once
#include <cstdint>
#include <limits>
#include <type_traits>
#include "registern_runtime.hpp"

namespace chimera::runtime {

template <std::size_t Bits>
class RegisterMachine {
    static_assert(Bits % 64 == 0, "Register width must be a multiple of 64 bits");
public:
    using Reg = WideRegister<Bits>;
    static constexpr std::size_t kLimbs = Bits / 64;

    void clear() noexcept { acc_.clear(); }
    const Reg& accumulator() const noexcept { return acc_; }

    void execute(const DecodedInstruction& ins) noexcept {
        switch (ins.op) {
        case MicroOp::Nop: break;
        case MicroOp::Add: add(ins); break;
        case MicroOp::Sub: sub(ins); break;
        case MicroOp::And: bit_and(ins); break;
        case MicroOp::Or: bit_or(ins); break;
        case MicroOp::Xor: bit_xor(ins); break;
        case MicroOp::Shl: shl(ins); break;
        case MicroOp::Shr: shr(ins); break;
        }
    }
private:
    Reg acc_{};

    static std::uint64_t operand(const DecodedInstruction& i, unsigned n) noexcept {
        return n == 0 ? i.imm : (n == 1 ? i.aux : 0);
    }
    void add(const DecodedInstruction& i) noexcept {
        std::uint64_t x = acc_.low();
        std::uint64_t y = operand(i, 0);
        acc_.clear();
        acc_.limbs[0] = x + y;
    }
    void sub(const DecodedInstruction& i) noexcept {
        std::uint64_t x = acc_.low();
        std::uint64_t y = operand(i, 0);
        acc_.clear();
        acc_.limbs[0] = x - y;
    }
    void bit_and(const DecodedInstruction& i) noexcept { apply(i, [](auto a, auto b){ return a & b; }); }
    void bit_or(const DecodedInstruction& i) noexcept { apply(i, [](auto a, auto b){ return a | b; }); }
    void bit_xor(const DecodedInstruction& i) noexcept { apply(i, [](auto a, auto b){ return a ^ b; }); }
    void shl(const DecodedInstruction& i) noexcept { acc_.limbs[0] <<= (i.imm & 63u); }
    void shr(const DecodedInstruction& i) noexcept { acc_.limbs[0] >>= (i.imm & 63u); }
    template<class F> void apply(const DecodedInstruction& i, F f) noexcept {
        acc_.limbs[0] = f(acc_.limbs[0], i.imm);
    }
};

} // namespace chimera::runtime
