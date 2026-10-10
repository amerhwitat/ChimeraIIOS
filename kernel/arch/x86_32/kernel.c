/* Early serial-only probe for the x86-32 bring-up target.
 * Production memory management, GDT/IDT, interrupts, drivers and scheduler
 * are deliberately not claimed by this probe. */
#include <stdint.h>

static inline void outb(uint16_t port, uint8_t value) {
    __asm__ volatile ("outb %0, %1" : : "a"(value), "Nd"(port));
}
static inline uint8_t inb(uint16_t port) {
    uint8_t value;
    __asm__ volatile ("inb %1, %0" : "=a"(value) : "Nd"(port));
    return value;
}

static void serial_init(void) {
    outb(0x3F8 + 1, 0x00);
    outb(0x3F8 + 3, 0x80);
    outb(0x3F8 + 0, 0x03);
    outb(0x3F8 + 1, 0x00);
    outb(0x3F8 + 3, 0x03);
    outb(0x3F8 + 2, 0xC7);
    outb(0x3F8 + 4, 0x0B);
}

static void serial_write(const char *s) {
    while (*s) {
        /* Bound each poll so a missing UART cannot hang the bring-up probe. */
        uint32_t spins = 100000u;
        while (spins-- && !(inb(0x3FD) & 0x20u)) { }
        if (spins != 0u) outb(0x3F8, (uint8_t)*s);
        ++s;
    }
}

void koronos32_main(void) {
    serial_init();
    serial_write("KORONOS32_BOOT_OK\r\n");
    serial_write("KORONOS32_STAGE=serial-probe-only\r\n");
    for (;;) __asm__ volatile ("cli; hlt");
}
