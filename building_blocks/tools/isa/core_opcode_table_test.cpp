#include <cassert>
#include "core_opcode_table.cpp"

int main() {
    const auto* add = chimera::isa::find(0x01);
    const auto* trap = chimera::isa::find(0x0E);
    assert(add && add->mnemonic == "ADD");
    assert(trap && trap->mnemonic == "TRAP");
    assert(chimera::isa::find(0xFFFF) == nullptr);
}
