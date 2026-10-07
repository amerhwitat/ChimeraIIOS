#include "chimera/nbit_isa.hpp"
#include <cassert>
#include <iostream>
#include <fstream>

int main(){
    chimera::isa::NBitISACatalog c;
    std::string error;
    const char* candidates[] = {
        "tools/isa/local_isa_catalog.json",
        "../tools/isa/local_isa_catalog.json"
    };
    bool loaded = false;
    for (const char* path : candidates) {
        if (std::ifstream(path).good()) {
            loaded = c.load_file(path, &error);
            if (loaded) break;
            error.clear();
        }
    }
    assert(loaded);
    assert(error.empty());
    assert(c.find_width(64));
    assert(c.find_width(8192));
    assert(c.find_width(16384));
    assert(c.find_width(65536));
    assert(chimera::isa::valid_nbit_width(8));
    assert(chimera::isa::valid_nbit_width(16384));
    assert(!chimera::isa::valid_nbit_width(7));
    assert(!chimera::isa::valid_nbit_width(65537));
    assert(c.find("chimera-risc-n16384")->style==chimera::isa::ISAStyle::RISC);
    std::cout<<"N-bit ISA catalog: PASS\n";
}
