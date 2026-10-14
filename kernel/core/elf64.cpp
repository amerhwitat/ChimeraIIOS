#include "../include/chimera/elf64.h"

static volatile uint32_t elf64_state;

extern "C" void koronos_elf64_init(void) {
    elf64_state = 0x454C4634u;
}

extern "C" int koronos_elf64_validate(const void *image, uint64_t size,
                                      uint16_t machine) {
    if (!image || size < sizeof(koronos_elf64_ehdr)) return 0;

    koronos_elf64_ehdr h{};
    __builtin_memcpy(&h, image, sizeof(h));
    if (!koronos_elf64_valid(&h) ||
        h.e_version != 1u ||
        h.e_ehsize != sizeof(koronos_elf64_ehdr) ||
        h.e_machine != machine ||
        h.e_phentsize != sizeof(koronos_elf64_phdr)) {
        return 0;
    }

    // Check with subtraction/division rather than multiplying attacker-controlled
    // fields or adding e_phoff + table_size, both of which can overflow.
    if (h.e_phoff > size) return 0;
    if (h.e_phnum > (size - h.e_phoff) / sizeof(koronos_elf64_phdr)) {
        return 0;
    }

    return 1;
}
