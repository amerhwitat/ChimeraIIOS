#pragma once
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace chimera::isa {

struct BitField {
    std::string name;
    std::uint16_t start = 0;
    std::uint16_t end = 0;
    std::uint16_t width = 0;
    std::string mask_hex;
    std::uint16_t shift = 0;
};

struct BitfieldInstruction {
    std::string mnemonic;
    std::uint16_t opcode = 0;
    std::string encoding_template;
    std::string encoding_status;
    std::vector<BitField> bitfields;
};

class BitfieldRegistry {
public:
    bool load_json(std::string_view json, std::string* error = nullptr);
    bool load_file(const std::string& path, std::string* error = nullptr);
    const BitfieldInstruction* by_opcode(std::uint16_t opcode) const noexcept;
    const BitfieldInstruction* by_mnemonic(std::string_view mnemonic) const noexcept;
    std::size_t size() const noexcept { return instructions_.size(); }
    bool abi_is_canonical() const noexcept { return abi_bytes_ == 16 && abi_layout_ == "opcode[16] | rd[16] | rs[16] | rt[16] | immediate[64]"; }
    const std::string& abi_layout() const noexcept { return abi_layout_; }

private:
    std::vector<BitfieldInstruction> instructions_;
    std::uint32_t abi_bytes_ = 0;
    std::string abi_layout_;
};

std::uint64_t extract_bits(std::uint64_t word, std::uint16_t shift, std::uint16_t width) noexcept;
std::uint64_t insert_bits(std::uint64_t word, std::uint64_t value, std::uint16_t shift, std::uint16_t width) noexcept;

} // namespace chimera::isa
