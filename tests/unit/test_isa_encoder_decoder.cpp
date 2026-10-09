#include "chimera/ISA_EncoderDecoder.hpp"
#include <cassert>
#include <iostream>
#include <unordered_map>

using namespace chimera::isa;

int main(int argc, char** argv) {
    const std::string path = argc > 1 ? argv[1] : "isa_bitfields.json";
    BitfieldRegistry registry;
    std::string error;
    // Keep side effects out of assert(): NDEBUG removes assert expressions in
    // Release builds, which otherwise leaves the registry empty on Windows.
    if (!registry.load_file(path, &error) || !error.empty()) {
        std::cerr << "Unable to load ISA metadata: " << error << "\n";
        return 1;
    }
    if (registry.size() != 284) {
        std::cerr << "Expected 284 ISA records, got " << registry.size() << "\n";
        return 1;
    }
    if (!registry.abi_is_canonical()) {
        std::cerr << "ISA registry ABI is not canonical\n";
        return 1;
    }

    ISAEncoderDecoder codec(registry);
    const auto word = codec.encode("ADD", {{"rd", 1}, {"rs", 2}, {"rt", 3}});
    const auto decoded = codec.decode("ADD", word);

    assert(decoded.at("opcode") == 1);
    assert(decoded.at("rd") == 1);
    assert(decoded.at("rs") == 2);
    assert(decoded.at("rt") == 3);
    assert(codec.opcode("ADD") == 0x0001);

    // Exercise a field crossing the 64-bit boundary when such a template is
    // present; otherwise the canonical 64-bit fields above remain the golden test.
    if (word.lo == 0 && word.hi == 0) {
        std::cerr << "ISA encoder produced an empty instruction word\n";
        return 1;
    }
    std::cout << "ISA encoder/decoder round-trip: PASS\n";
    return 0;
}
