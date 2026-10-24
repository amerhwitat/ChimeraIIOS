/* Early serial-only probe for the x86-32 bring-up target.
 * Production memory management, GDT/IDT, interrupts, drivers and scheduler
 * are deliberately not claimed by this probe. */
#include <stdint.h>

#define COM1_BASE 0x3F8u
#define UART_LSR  5u
#define UART_LSR_THRE 0x20u

static inline void outb(uint16_t port, uint8_t value) {
    __asm__ volatile ("outb %0, %1" : : "a"(value), "Nd"(port));
}

static inline uint8_t inb(uint16_t port) {
    uint8_t value;
    __asm__ volatile ("inb %1, %0" : "=a"(value) : "Nd"(port));
    return value;
}

static void serial_init(void) {
    outb(COM1_BASE + 1, 0x00);
    outb(COM1_BASE + 3, 0x80);
    outb(COM1_BASE + 0, 0x03);
    outb(COM1_BASE + 1, 0x00);
    outb(COM1_BASE + 3, 0x03);
    outb(COM1_BASE + 2, 0xC7);
    outb(COM1_BASE + 4, 0x0B);
}

/* Wait for the 16550 transmitter holding register to become empty before
 * each byte. Blind consecutive OUTs can overrun the FIFO and drop the very
 * boot marker that the QEMU harness uses as its acceptance signal. */
static void serial_write(const char *s) {
    while (*s) {
        while ((inb(COM1_BASE + UART_LSR) & UART_LSR_THRE) == 0) {
            __asm__ volatile ("pause");
        }
        outb(COM1_BASE, (uint8_t)*s++);
    }
}

void koronos32_main(void) {
    serial_init();
    serial_write("KORONOS32_BOOT_OK\r\n");
    serial_write("KORONOS32_STAGE=serial-probe-only\r\n");
    for (;;) __asm__ volatile ("cli; hlt");
}
