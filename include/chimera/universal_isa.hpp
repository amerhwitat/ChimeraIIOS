#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace chimera::universal_isa {

enum class Family : std::uint8_t { Chimera, X86, ARM, RiscV, MIPS, Power, SPARC, S390, M68K, Alpha, PA_RISC, SuperH, Itanium, AVR, Xtensa, Wasm, GPU, Legacy };
enum class Execution : std::uint8_t { Native, Translated, Emulated, Imported };

struct Target {
    std::string_view name;
    Family family;
    std::uint16_t natural_width;
    bool variable_encoding;
    Execution execution;
};

struct InstructionEncoding {
    std::uint32_t opcode;
    std::uint8_t length;
    std::uint8_t operand_count;
    std::uint16_t flags;
    std::array<std::uint8_t, 16> bytes{};
};

inline constexpr Target kTargets[] = {
    {"chimera-r8192", Family::Chimera, 8192, false, Execution::Native},
    {"chimera-c8192", Family::Chimera, 8192, true, Execution::Native},
    {"x86-64", Family::X86, 64, true, Execution::Translated},
    {"aarch64", Family::ARM, 64, false, Execution::Translated},
    {"riscv64", Family::RiscV, 64, true, Execution::Translated},
    {"mips64", Family::MIPS, 64, false, Execution::Translated},
    {"power64", Family::Power, 64, true, Execution::Translated},
    {"sparc64", Family::SPARC, 64, false, Execution::Translated},
    {"s390x", Family::S390, 64, true, Execution::Translated},
    {"m68k", Family::M68K, 32, true, Execution::Emulated},
    {"alpha", Family::Alpha, 64, false, Execution::Emulated},
    {"parisc64", Family::PA_RISC, 64, false, Execution::Emulated},
    {"sh4", Family::SuperH, 32, false, Execution::Emulated},
    {"itanium", Family::Itanium, 64, true, Execution::Emulated},
    {"avr", Family::AVR, 8, true, Execution::Emulated},
    {"xtensa", Family::Xtensa, 32, true, Execution::Emulated},
    {"wasm32", Family::Wasm, 32, true, Execution::Imported},
};

constexpr std::size_t target_count() noexcept { return sizeof(kTargets) / sizeof(kTargets[0]); }
const Target* find_target(std::string_view name) noexcept;

// Canonical native encodings are deliberately independent of foreign encodings.
// Foreign CPU instructions are imported into this registry and lowered to micro-ops.
InstructionEncoding encode_native(std::uint16_t opcode, std::uint16_t dst, std::uint16_t src_a, std::uint16_t src_b, std::uint64_t imm = 0, std::uint8_t imm_len = 0) noexcept;

} // namespace chimera::universal_isa
