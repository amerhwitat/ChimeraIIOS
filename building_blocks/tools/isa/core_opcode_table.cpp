#include <array>
#include <cstdint>
#include <string_view>

namespace chimera::isa {

struct OpcodeSpec {
    std::string_view mnemonic;
    std::uint16_t opcode;
    std::string_view family;
};

inline constexpr std::array<OpcodeSpec, 16> core = {{
    {"NOP", 0x0000, "control"}, {"ADD", 0x0001, "integer"},
    {"SUB", 0x0002, "integer"}, {"MUL", 0x0003, "integer"},
    {"DIV", 0x0004, "integer"}, {"LOAD", 0x0010, "memory"},
    {"STORE", 0x0011, "memory"}, {"FENCE", 0x0020, "ordering"},
    {"ATOMIC_CAS", 0x0021, "atomic"}, {"NETSEND", 0x0030, "network"},
    {"NETRECV", 0x0031, "network"}, {"SPAWN", 0x0040, "scheduler"},
    {"WAIT", 0x0041, "scheduler"}, {"SYSCALL", 0x0050, "system"},
    {"TRAP", 0x0051, "system"}, {"TCONTRACT", 0x0060, "tensor"}
}};

constexpr const OpcodeSpec* find(std::uint16_t opcode) noexcept {
    for (const auto& item : core) if (item.opcode == opcode) return &item;
    return nullptr;
}

} // namespace chimera::isa
