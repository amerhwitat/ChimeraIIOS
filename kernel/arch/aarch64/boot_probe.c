/* QEMU virt PL011 early-console probe. This is an architecture bring-up test,
 * not the complete Koronos kernel or userspace. */
typedef unsigned int u32;
#define PL011_BASE 0x09000000UL
#define PL011_DR (*(volatile u32 *)(PL011_BASE + 0x00))
#define PL011_FR (*(volatile u32 *)(PL011_BASE + 0x18))
static void putc_uart(char c) {
    while (PL011_FR & (1u << 5)) { }
    PL011_DR = (u32)(unsigned char)c;
}
static void puts_uart(const char *s) { while (*s) putc_uart(*s++); }
__attribute__((noreturn)) void koronos_boot(unsigned long dtb) {
    (void)dtb;
    puts_uart("\r\nKORONOS_AARCH64_ENTRY_OK\r\n");
    puts_uart("STAGE=architecture-bringup-probe-only\r\n");
    for (;;) __asm__ volatile("wfi");
}
