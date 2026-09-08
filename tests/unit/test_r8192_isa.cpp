#include "chimera/isa8192.hpp"
#include <cassert>
#include <cstdint>
#include <stdexcept>

int main() {
    using namespace chimera;
    // Canonical fetch packets are always 16 bytes: 64-bit header + 64-bit immediate/reserved tail.
    const std::uint8_t add[16] = {0x01,0x00,0x01,0x00,0x01,0x00,0x02,0x00,0,0,0,0,0,0,0,0};
    const Instr decoded = decode(add,sizeof(add));
    assert(decoded.opcode==0x0001 && decoded.dst==1 && decoded.srcA==1 && decoded.srcB==2);
    assert(decoded.length==16);
    bool rejected=false;
    try { (void)decode(add,8); } catch(const std::invalid_argument&) { rejected=true; }
    assert(rejected);
    assert(is_defined_opcode(0x0001));
    assert(is_defined_opcode(0x0046));
    assert(is_defined_opcode(0x00A8));
    assert(is_defined_opcode(0x011C));
    assert(!is_defined_opcode(0x0000));
    assert(!is_defined_opcode(0x011D));
    const auto *meta=opcode_info(0x003D);
    assert(meta && meta->mnemonic=="SHA256" && meta->latency==40 && meta->throughput==0.05 && meta->pipeline_stage=="CRYPTO");
    const auto *priv=opcode_info(0x0103);
    assert(priv && priv->privileged);
    return 0;
}
