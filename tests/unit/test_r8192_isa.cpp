#include "chimera/isa8192.hpp"
#include <cassert>
#include <cstdint>

int main() {
    using namespace chimera;

    // Canonical Chimera-II fetch packets use a 16-bit little-endian opcode.
    const std::uint8_t add[] = {0x01, 0x00, 0x01, 0x00, 0x01, 0x00, 0x02, 0x00};
    const Instr decoded = decode(add, sizeof(add));
    assert(decoded.opcode == 0x0001);
    assert(decoded.dst == 1);
    assert(decoded.srcA == 1);
    assert(decoded.srcB == 2);
    assert(decoded.length == 8);

    // The extended table must recognize the complete supplied opcode range.
    assert(is_defined_opcode(0x0001));
    assert(is_defined_opcode(0x0046));
    assert(is_defined_opcode(0x00A8));
    assert(is_defined_opcode(0x011C));
    assert(!is_defined_opcode(0x011D));

    const auto *meta = opcode_info(0x003D);
    assert(meta != nullptr);
    assert(meta->mnemonic == "SHA256");
    assert(meta->latency == 40);
    assert(meta->throughput == 0.05);
    assert(meta->pipeline_stage == "CRYPTO");

    const auto *priv = opcode_info(0x0103);
    assert(priv != nullptr);
    assert(priv->privileged);

    return 0;
}
