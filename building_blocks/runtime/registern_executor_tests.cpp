#include "registern_executor.hpp"
#include <cassert>

int main() {
    chimera::runtime::RegisterMachine<8192> m;
    chimera::runtime::DecodedInstruction add{chimera::runtime::MicroOp::Add, 7, 0};
    m.execute(add);
    assert(m.accumulator().low() == 7);
    chimera::runtime::DecodedInstruction shl{chimera::runtime::MicroOp::Shl, 3, 0};
    m.execute(shl);
    assert(m.accumulator().low() == 56);
}
