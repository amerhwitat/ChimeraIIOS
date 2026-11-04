#include "chimera/physmap.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

int main() {
    assert(koronos_physmap_ready() == 0);
    assert(koronos_phys_to_virt(0x1000, 4096) == nullptr);
    assert(koronos_physmap_validate_range(0, 1) == 0);
    assert(koronos_physmap_validate_range(0xFFFFF000ull, 4096) == 0);
    assert(koronos_physmap_validate_range(0x100000000ull, 1) < 0);
    assert(koronos_physmap_validate_range(0xFFFFF000ull, 8192) < 0);
    assert(koronos_physmap_validate_range(0, 0) < 0);
    puts("Koronos physmap range contract passed");
    return 0;
}
