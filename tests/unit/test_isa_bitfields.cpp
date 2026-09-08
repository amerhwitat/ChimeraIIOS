#include "chimera/isa_bitfields.hpp"
#include <cassert>
#include <iostream>

int main(int argc, char** argv) {
    assert(chimera::isa::extract_bits(0x01010203ULL, 24, 8) == 0x01);
    assert(chimera::isa::extract_bits(0x01010203ULL, 16, 8) == 0x01);
    assert(chimera::isa::insert_bits(0, 0x01, 24, 8) == 0x01000000ULL);

    if (argc > 1) {
        chimera::isa::BitfieldRegistry registry;
        std::string error;
        assert(registry.load_file(argv[1], &error) && !error.size());
        assert(registry.abi_is_canonical());
        assert(registry.by_mnemonic("ADD") != nullptr);
        assert(registry.by_opcode(0x0001) != nullptr);
    }
    std::cout << "PASS: ISA bitfield JSON reader and mask helpers\n";
    return 0;
}
