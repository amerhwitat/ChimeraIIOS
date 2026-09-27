#include "chimera/ISA_EncoderDecoder.hpp"

#include <algorithm>
#include <cctype>
#include <limits>
#include <stdexcept>

namespace chimera::isa {
namespace {

std::uint64_t width_mask(std::uint16_t width) {
    if (width == 0) return 0;
    if (width >= 64) return std::numeric_limits<std::uint64_t>::max();
    return (std::uint64_t{1} << width) - 1;
}

} // namespace

bool ISAEncoderDecoder::supported_for_template_encoding(const BitfieldInstruction& instruction) noexcept {
    if (instruction.encoding_status != "template") return false;
    for (const auto& field : instruction.bitfields) {
        if (field.width == 0 || field.end < field.start || field.end >= 128) return false;
        if (field.width > 64) return false; // current public operand API is uint64_t
    }
    return true;
}

std::uint64_t ISAEncoderDecoder::parse_mask64(const BitField& field) {
    // Generated ISA metadata may represent a 64-bit mask in a zero-extended
    // 128-bit hexadecimal form. std::stoull() throws on such strings even when
    // all significant bits fit in uint64_t, which used to abort the CTest
    // encoder/decoder subprocess. Parse explicitly and reject only non-zero
    // bits above bit 63.
    if (field.mask_hex.empty())
        throw std::runtime_error("empty bitfield mask: " + field.name);

    std::string hex = field.mask_hex;
    if (hex.size() >= 2 && hex[0] == '0' && (hex[1] == 'x' || hex[1] == 'X'))
        hex.erase(0, 2);
    if (hex.empty())
        throw std::runtime_error("empty bitfield mask: " + field.name);

    // Ignore leading zeroes so canonical 128-bit masks remain accepted.
    const auto first_nonzero = hex.find_first_not_of('0');
    if (first_nonzero == std::string::npos)
        return 0;
    hex.erase(0, first_nonzero);

    // More than 16 significant hexadecimal digits means at least one bit
    // above uint64_t. Such a mask is incompatible with this public API.
    if (hex.size() > 16)
        throw std::runtime_error("bitfield mask exceeds uint64_t: " + field.name);

    std::uint64_t value = 0;
    for (const char c : hex) {
        unsigned digit = 0;
        if (c >= '0' && c <= '9') digit = static_cast<unsigned>(c - '0');
        else if (c >= 'a' && c <= 'f') digit = static_cast<unsigned>(c - 'a') + 10;
        else if (c >= 'A' && c <= 'F') digit = static_cast<unsigned>(c - 'A') + 10;
        else throw std::runtime_error("invalid hexadecimal bitfield mask: " + field.name);
        value = (value << 4) | digit;
    }
    return value;
}

std::uint64_t ISAEncoderDecoder::get_field(const InstructionWord128& word,
                                           std::uint16_t start, std::uint16_t width) {
    if (width == 0 || width > 64 || start >= 128 || static_cast<std::uint32_t>(start) + width > 128)
        throw std::runtime_error("unsupported bitfield range");
    if (start < 64) {
        if (static_cast<std::uint32_t>(start) + width <= 64)
            return (word.lo >> start) & width_mask(width);
        const auto low_width = static_cast<std::uint16_t>(64 - start);
        const auto high_width = static_cast<std::uint16_t>(width - low_width);
        const auto low = (word.lo >> start) & width_mask(low_width);
        const auto high = word.hi & width_mask(high_width);
        return low | (high << low_width);
    }
    return (word.hi >> (start - 64)) & width_mask(width);
}

void ISAEncoderDecoder::put_field(InstructionWord128& word, std::uint64_t value,
                                  std::uint16_t start, std::uint16_t width) {
    if (width == 0 || width > 64 || start >= 128 || static_cast<std::uint32_t>(start) + width > 128)
        throw std::runtime_error("unsupported bitfield range");
    value &= width_mask(width);
    if (start < 64) {
        if (static_cast<std::uint32_t>(start) + width <= 64) {
            const auto mask = width_mask(width) << start;
            word.lo = (word.lo & ~mask) | (value << start);
            return;
        }
        const auto low_width = static_cast<std::uint16_t>(64 - start);
        const auto high_width = static_cast<std::uint16_t>(width - low_width);
        const auto low_mask = width_mask(low_width) << start;
        word.lo = (word.lo & ~low_mask) | ((value & width_mask(low_width)) << start);
        const auto high_mask = width_mask(high_width);
        word.hi = (word.hi & ~high_mask) | ((value >> low_width) & high_mask);
        return;
    }
    const auto shift = static_cast<std::uint16_t>(start - 64);
    const auto mask = width_mask(width) << shift;
    word.hi = (word.hi & ~mask) | (value << shift);
}

InstructionWord128 ISAEncoderDecoder::encode(
    std::string_view mnemonic,
    const std::unordered_map<std::string, std::uint64_t>& operands) const {
    const auto* instruction = registry_.by_mnemonic(mnemonic);
    if (!instruction) throw std::runtime_error("Unknown mnemonic: " + std::string(mnemonic));
    if (!supported_for_template_encoding(*instruction))
        throw std::runtime_error("Encoding metadata is not approved for template assembly: " + instruction->mnemonic);

    InstructionWord128 word{};
    for (const auto& field : instruction->bitfields) {
        if (field.name == "opcode") {
            put_field(word, instruction->opcode, field.start, field.width);
            continue;
        }
        const auto it = operands.find(field.name);
        if (it == operands.end())
            throw std::runtime_error("Missing operand: " + field.name);
        const auto value = it->second;
        if (field.width < 64 && (value >> field.width) != 0)
            throw std::runtime_error("Operand does not fit field: " + field.name);
        // Validate the declared mask without rejecting zero-extended 128-bit
        // representations of masks whose significant value fits uint64_t.
        (void)parse_mask64(field);
        put_field(word, value, field.start, field.width);
    }
    return word;
}

std::unordered_map<std::string, std::uint64_t>
ISAEncoderDecoder::decode(std::string_view mnemonic, InstructionWord128 word) const {
    const auto* instruction = registry_.by_mnemonic(mnemonic);
    if (!instruction) throw std::runtime_error("Unknown mnemonic: " + std::string(mnemonic));
    if (!supported_for_template_encoding(*instruction))
        throw std::runtime_error("Encoding metadata is not approved for template decoding: " + instruction->mnemonic);

    std::unordered_map<std::string, std::uint64_t> result;
    for (const auto& field : instruction->bitfields)
        result[field.name] = get_field(word, field.start, field.width);
    return result;
}

std::uint16_t ISAEncoderDecoder::opcode(std::string_view mnemonic) const {
    const auto* instruction = registry_.by_mnemonic(mnemonic);
    if (!instruction) throw std::runtime_error("Unknown mnemonic: " + std::string(mnemonic));
    return instruction->opcode;
}

} // namespace chimera::isa
