#include "boot_info.hpp"
#include <cassert>

int main() {
    chimera::boot::BootInfo b{};
    b.memory_bytes = 1024ull * 1024ull;
    b.cpu_count = 1;
    b.flags = chimera::boot::UEFI | chimera::boot::SECURE_BOOT;
    assert(chimera::boot::valid(b));
}
