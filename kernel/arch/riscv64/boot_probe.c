/* QEMU virt 16550 early-console probe. This is an architecture bring-up test,
 * not the complete Koronos kernel or userspace. */
static void putc_uart(char c) {
    *(volatile unsigned char *)0x10000000UL = (unsigned char)c;
}
static void puts_uart(const char *s) { while (*s) putc_uart(*s++); }
__attribute__((noreturn)) void koronos_boot(unsigned long dtb) {
    (void)dtb;
    puts_uart("\r\nKORONOS_RISCV64_ENTRY_OK\r\n");
    puts_uart("STAGE=architecture-bringup-probe-only\r\n");
    for (;;) __asm__ volatile("wfi");
}
