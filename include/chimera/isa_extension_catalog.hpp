#pragma once

#include <algorithm>
#include <array>
#include <string_view>
#include <vector>

namespace chimera::isa {

enum class Family { CISC, RISC, Hybrid };

enum class InstructionClass {
    Integer, BitManip, Atomics, MemoryOrder, BranchControl, StringMemory,
    Vector, MatrixTensor, FloatingPoint, Decimal, Crypto, SystemControl,
    Virtualization, CacheMemory, Synchronization, Network, Predicate
};

struct InstructionDescriptor {
    std::string_view mnemonic;
    std::string_view extension;
    InstructionClass kind;
    Family family;
};

class ExtensionCatalog {
public:
    constexpr bool contains(std::string_view extension) const noexcept {
        for (const auto &e : extensions_) if (e == extension) return true;
        return false;
    }

    constexpr bool contains_instruction(std::string_view mnemonic) const noexcept {
        for (const auto &i : instructions_) if (i.mnemonic == mnemonic) return true;
        return false;
    }

    constexpr const auto &instructions() const noexcept { return instructions_; }

private:
    static constexpr std::array<std::string_view, 15> extensions_ = {
        "BITMANIP", "ATOMICS", "MEMORY_ORDER", "VECTOR", "CRYPTO",
        "STRING_MEMORY", "SYSTEM_CONTROL", "VIRTUALIZATION", "DECIMAL",
        "MATRIX_TENSOR", "FLOATING_POINT", "CACHE_MEMORY", "BRANCH_CONTROL",
        "PREDICATE", "NETWORK"
    };

    static constexpr std::array<InstructionDescriptor, 31> instructions_ = {{
        {"ADD", "CORE", InstructionClass::Integer, Family::Hybrid},
        {"MUL", "CORE", InstructionClass::Integer, Family::Hybrid},
        {"TCONTRACT", "MATRIX_TENSOR", InstructionClass::MatrixTensor, Family::Hybrid},
        {"MODEXP", "CRYPTO", InstructionClass::Crypto, Family::Hybrid},
        {"NETSEND", "NETWORK", InstructionClass::Network, Family::Hybrid},
        {"CLZ", "BITMANIP", InstructionClass::BitManip, Family::RISC},
        {"CTZ", "BITMANIP", InstructionClass::BitManip, Family::RISC},
        {"POPCNT", "BITMANIP", InstructionClass::BitManip, Family::Hybrid},
        {"BEXT", "BITMANIP", InstructionClass::BitManip, Family::RISC},
        {"BDEP", "BITMANIP", InstructionClass::BitManip, Family::RISC},
        {"CAS", "ATOMICS", InstructionClass::Atomics, Family::Hybrid},
        {"SWAP", "ATOMICS", InstructionClass::Atomics, Family::Hybrid},
        {"FENCE", "MEMORY_ORDER", InstructionClass::MemoryOrder, Family::RISC},
        {"LFENCE", "MEMORY_ORDER", InstructionClass::MemoryOrder, Family::CISC},
        {"SFENCE", "MEMORY_ORDER", InstructionClass::MemoryOrder, Family::CISC},
        {"VADD", "VECTOR", InstructionClass::Vector, Family::RISC},
        {"VMUL", "VECTOR", InstructionClass::Vector, Family::RISC},
        {"VREDUCE", "VECTOR", InstructionClass::Vector, Family::RISC},
        {"AESENC", "CRYPTO", InstructionClass::Crypto, Family::CISC},
        {"AESDEC", "CRYPTO", InstructionClass::Crypto, Family::CISC},
        {"CRC32", "CRYPTO", InstructionClass::Crypto, Family::Hybrid},
        {"SHA256", "CRYPTO", InstructionClass::Crypto, Family::Hybrid},
        {"MOVS", "STRING_MEMORY", InstructionClass::StringMemory, Family::CISC},
        {"CMPS", "STRING_MEMORY", InstructionClass::StringMemory, Family::CISC},
        {"PREFETCH", "CACHE_MEMORY", InstructionClass::CacheMemory, Family::Hybrid},
        {"TLBI", "SYSTEM_CONTROL", InstructionClass::SystemControl, Family::RISC},
        {"SYSCALL", "SYSTEM_CONTROL", InstructionClass::SystemControl, Family::Hybrid},
        {"VMRUN", "VIRTUALIZATION", InstructionClass::Virtualization, Family::Hybrid},
        {"VMEXIT", "VIRTUALIZATION", InstructionClass::Virtualization, Family::Hybrid},
        {"MADD", "MATRIX_TENSOR", InstructionClass::MatrixTensor, Family::Hybrid},
        {"VPERM", "VECTOR", InstructionClass::Vector, Family::Hybrid}
    }};
};

inline constexpr ExtensionCatalog extension_catalog{};

} // namespace chimera::isa
