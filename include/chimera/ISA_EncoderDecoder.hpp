#pragma once
#include "chimera/isa_bitfields.hpp"

#include <cstdint>
#include <string>
#include <string_view>
#include <unordered_map>

namespace chimera::isa {

// Canonical logical instruction container. The emulator ABI remains 16 bytes;
// lo contains bits [63:0] and hi contains bits [127:64].
struct InstructionWord128 {
    std::uint64_t lo = 0;
    std::uint64_t hi = 0;

    friend constexpr bool operator==(const InstructionWord128&, const InstructionWord128&) = default;
};

// Schema-driven assembler/disassembler facade. It consumes the same registry
// used by the existing tooling and deliberately refuses entries whose encoding
// metadata is not safe for logical-template assembly.
class ISAEncoderDecoder {
public:
    explicit ISAEncoderDecoder(const BitfieldRegistry& registry) noexcept : registry_(registry) {}

    InstructionWord128 encode(std::string_view mnemonic,
                              const std::unordered_map<std::string, std::uint64_t>& operands) const;

    std::unordered_map<std::string, std::uint64_t>
    decode(std::string_view mnemonic, InstructionWord128 word) const;

    std::uint16_t opcode(std::string_view mnemonic) const;

private:
    const BitfieldRegistry& registry_;

    static bool supported_for_template_encoding(const BitfieldInstruction& instruction) noexcept;
    static std::uint64_t parse_mask64(const BitField& field);
    static std::uint64_t get_field(const InstructionWord128& word, std::uint16_t start, std::uint16_t width);
    static void put_field(InstructionWord128& word, std::uint64_t value,
                          std::uint16_t start, std::uint16_t width);
};

} // namespace chimera::isa
