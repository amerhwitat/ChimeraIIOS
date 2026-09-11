#include "registern_runtime.hpp"
#include <cassert>

int main() {
    chimera::runtime::WideRegister<8192> r;
    r.clear();
    assert(r.low() == 0);
    chimera::runtime::DecodedInstruction d{};
    d.op = chimera::runtime::MicroOp::Add;
    d.imm = 1;
    assert(d.imm == 1);
}
