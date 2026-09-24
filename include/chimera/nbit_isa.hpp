#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace chimera::isa {

enum class ISAStyle : std::uint8_t { RISC, CISC, Hybrid };

struct NBitFormat {
    std::uint16_t opcode_bits{16};
    std::uint16_t register_index_bits{16};
    std::uint16_t immediate_bits{64};
    std::uint16_t min_instruction_bytes{16};
    std::uint16_t max_instruction_bytes{16};
    bool variable_length{false};
};

struct NBitProfile {
    std::string name;
    std::string source;
    ISAStyle style{ISAStyle::Hybrid};
    std::size_t register_bits{64};
    std::size_t min_register_bits{8};
    std::size_t max_register_bits{64};
    NBitFormat format{};
    bool hardware_native{false};
};

class NBitISACatalog {
public:
    bool load_file(const std::string& path, std::string* error = nullptr);
    bool load_json(std::string_view json, std::string* error = nullptr);
    const NBitProfile* find(std::string_view name) const noexcept;
    const NBitProfile* find_width(std::size_t bits) const noexcept;
    std::size_t size() const noexcept { return profiles_.size(); }
    const std::vector<NBitProfile>& profiles() const noexcept { return profiles_; }

private:
    std::vector<NBitProfile> profiles_;
};

constexpr bool valid_nbit_width(std::size_t bits) noexcept {
    return bits >= 8 && bits <= 65536 && (bits % 8) == 0;
}

// Returns true only for widths explicitly present in the generated local
// catalogue. Wider-than-silicon configurations are software-synthesized.
bool is_generated_width(const NBitISACatalog& catalog, std::size_t bits) noexcept;

} // namespace chimera::isa
