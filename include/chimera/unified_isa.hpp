#pragma once
#include <cstdint>
#include <string_view>
#include <array>

namespace chimera::isa {

enum class Family : uint8_t { Chimera8192, RV32I, RV64I, AArch64, X86_64 };
enum class Kind : uint8_t { Invalid, Integer, LoadStore, Branch, System, Atomic, Vector, Floating, Crypto, Control };

struct Instruction {
    Family family{Family::Chimera8192};
    Kind kind{Kind::Invalid};
    uint64_t raw{0};
    uint8_t length{0};
    uint16_t opcode{0};
    uint8_t rd{0}, rs1{0}, rs2{0};
    int64_t immediate{0};
    std::string_view mnemonic{};
};

struct DecoderResult { Instruction instruction{}; bool valid{false}; };

DecoderResult decode_riscv32(uint32_t word);
DecoderResult decode_riscv64(uint32_t word);
DecoderResult decode_x86_64(const uint8_t* bytes, std::size_t length);
DecoderResult decode_aarch64(uint32_t word);
std::string_view family_name(Family);
std::string_view kind_name(Kind);

// Architectural feature matrix used by the web explorer and kernel build system.
struct FeatureSet {
    bool integer=true, load_store=true, branches=true, atomics=false;
    bool floating=false, vector=false, crypto=false, privileged=false;
    bool variable_length=false, capability=false, tensor=false;
};
FeatureSet features(Family);

} // namespace chimera::isa
