#include "chimera/universal_isa.hpp"
#include <cstring>

namespace chimera::universal_isa {

const Target* find_target(std::string_view name) noexcept {
    for (const auto& target : kTargets) if (target.name == name) return &target;
    return nullptr;
}

InstructionEncoding encode_native(std::uint16_t opcode, std::uint16_t dst, std::uint16_t src_a, std::uint16_t src_b, std::uint64_t imm, std::uint8_t imm_len) noexcept {
    InstructionEncoding out{};
    out.opcode = opcode;
    out.length = static_cast<std::uint8_t>(8 + (imm_len ? 8 : 0));
    out.operand_count = 3;
    out.bytes[0] = static_cast<std::uint8_t>(opcode & 0xff);
    out.bytes[1] = static_cast<std::uint8_t>((opcode >> 8) & 0xff);
    out.bytes[2] = static_cast<std::uint8_t>(dst & 0xff);
    out.bytes[3] = static_cast<std::uint8_t>((dst >> 8) & 0xff);
    out.bytes[4] = static_cast<std::uint8_t>(src_a & 0xff);
    out.bytes[5] = static_cast<std::uint8_t>((src_a >> 8) & 0xff);
    out.bytes[6] = static_cast<std::uint8_t>(src_b & 0xff);
    out.bytes[7] = static_cast<std::uint8_t>((src_b >> 8) & 0xff);
    if (imm_len) std::memcpy(out.bytes.data() + 8, &imm, 8);
    return out;
}

} // namespace chimera::universal_isa
