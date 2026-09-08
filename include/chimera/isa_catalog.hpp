#pragma once
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace chimera::isa {

enum class Family : std::uint8_t { Chimera, RISCV, AArch64, X86_64, MIPS, POWER, SPARC, GPU, VAX };
enum class Class : std::uint8_t { RISC, CISC, Specialized };

struct Descriptor {
    std::string_view name;
    Family family;
    Class kind;
    std::uint16_t natural_width_bits;
    bool variable_length_encoding;
};

inline constexpr Descriptor kCatalog[] = {
    {"Chimera-R8192", Family::Chimera, Class::Specialized, 8192, true},
    {"RISC-V", Family::RISCV, Class::RISC, 64, true},
    {"AArch64", Family::AArch64, Class::RISC, 64, false},
    {"x86-64", Family::X86_64, Class::CISC, 64, true},
    {"MIPS", Family::MIPS, Class::RISC, 64, false},
    {"POWER", Family::POWER, Class::RISC, 64, true},
    {"SPARC", Family::SPARC, Class::RISC, 64, false},
    {"GPU-IR", Family::GPU, Class::Specialized, 32, true},
    {"VAX", Family::VAX, Class::CISC, 32, true},
};

inline constexpr std::size_t catalog_size() noexcept { return sizeof(kCatalog) / sizeof(kCatalog[0]); }

inline constexpr const Descriptor* find(std::string_view name) noexcept {
    for (const auto& entry : kCatalog) if (entry.name == name) return &entry;
    return nullptr;
}

} // namespace chimera::isa
