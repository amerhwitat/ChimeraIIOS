#include <stdint.h>

static volatile uint16_t *const vga = (uint16_t *)0xB8000;

void chimera_boot_main(uint32_t magic, uint32_t multiboot_info) {
    (void)multiboot_info;
    const char *msg = (magic == 0x36d76289u)
        ? "Chimera II OS bootstrap: Multiboot2 OK"
        : "Chimera II OS bootstrap: invalid Multiboot2 magic";
    for (uint32_t i = 0; msg[i] != 0; ++i) {
        vga[i] = (uint16_t)msg[i] | 0x0700u;
    }
}
