#pragma once
#include <cstdint>

namespace chimera::compat {

enum class ForeignArch : std::uint8_t {
    X86_64, AArch64, RiscV64, MIPS64, Power64, SPARC64, S390X,
    M68K, Alpha, PARISC, SuperH, Itanium, AVR, Xtensa, WebAssembly
};

enum class TranslationClass : std::uint8_t { Native, Lowered, Emulated, Unsupported };

struct TranslationResult {
    TranslationClass classification{TranslationClass::Unsupported};
    std::uint32_t micro_op_count{};
    bool preserves_memory_order{};
};

constexpr TranslationResult classify(ForeignArch arch) noexcept {
    switch (arch) {
        case ForeignArch::AArch64:
        case ForeignArch::RiscV64:
        case ForeignArch::X86_64:
            return {TranslationClass::Lowered, 1, true};
        default:
            return {TranslationClass::Emulated, 0, false};
    }
}

} // namespace chimera::compat
