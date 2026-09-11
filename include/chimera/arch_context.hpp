#pragma once
#include <array>
#include <cstdint>
#include "chimera/RegisterN.hpp"

namespace chimera::kernel {

enum class IsaMode : std::uint8_t { ChimeraR8192, ChimeraC8192, X86_64, AArch64, RiscV64, Other };

struct ArchContext {
    IsaMode mode{IsaMode::ChimeraR8192};
    std::uint64_t pc{};
    std::uint64_t flags{};
    std::array<std::uint64_t, 32> abi{};
    bool wide_state_live{false};
    Register8192 wide_scratch{};
};

void reset_arch_context(ArchContext&) noexcept;
void save_lazy_wide_state(ArchContext&, const Register8192&) noexcept;
const Register8192& wide_state(const ArchContext&) noexcept;

} // namespace chimera::kernel
