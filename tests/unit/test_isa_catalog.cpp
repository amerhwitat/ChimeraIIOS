#include "chimera/isa_catalog.hpp"
#include <cassert>

int main()
{
    using namespace chimera::isa;
    static_assert(catalog_size() >= 8);
    assert(find("RISC-V") != nullptr);
    assert(find("x86-64") != nullptr);
    assert(find("Chimera-R8192") != nullptr);
    assert(find("not-an-isa") == nullptr);
    return 0;
}
