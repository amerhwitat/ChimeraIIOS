#include <cassert>
#include "chimera/isa_extension_catalog.hpp"

int main() {
    using namespace chimera::isa;
    const auto &catalog = extension_catalog;

    assert(catalog.contains("BITMANIP"));
    assert(catalog.contains("ATOMICS"));
    assert(catalog.contains("MEMORY_ORDER"));
    assert(catalog.contains("VECTOR"));
    assert(catalog.contains("CRYPTO"));
    assert(catalog.contains("STRING_MEMORY"));
    assert(catalog.contains("SYSTEM_CONTROL"));
    assert(catalog.contains("VIRTUALIZATION"));
    assert(catalog.contains("DECIMAL"));
    assert(catalog.contains("MATRIX_TENSOR"));

    assert(catalog.contains_instruction("ADD"));
    assert(catalog.contains_instruction("MUL"));
    assert(catalog.contains_instruction("TCONTRACT"));
    assert(catalog.contains_instruction("MODEXP"));
    assert(catalog.contains_instruction("NETSEND"));

    assert(catalog.contains_instruction("CLZ"));
    assert(catalog.contains_instruction("CTZ"));
    assert(catalog.contains_instruction("CAS"));
    assert(catalog.contains_instruction("FENCE"));
    assert(catalog.contains_instruction("VADD"));
    assert(catalog.contains_instruction("AESENC"));
    assert(catalog.contains_instruction("CRC32"));
    assert(catalog.contains_instruction("PREFETCH"));
    assert(catalog.contains_instruction("VMRUN"));
    assert(catalog.contains_instruction("MADD"));
    return 0;
}
