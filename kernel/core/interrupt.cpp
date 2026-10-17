#include "chimera/interrupt.h"
#include "chimera/compat.h"

/* Defined by kernel/arch/x86_64/interrupts.asm.  Keep this declaration at
 * global scope: placing it inside the anonymous namespace gives the symbol
 * internal linkage and produces an undefined reference at link time. */
extern "C" void *chimera_isr_table[CHIMERA_IDT_ENTRIES];

namespace {

struct idt_gate64 {
    uint16_t offset_low;
    uint16_t selector;
    uint8_t ist;
    uint8_t type_attr;
    uint16_t offset_mid;
    uint32_t offset_high;
    uint32_t reserved;
} __attribute__((packed));

struct idt_ptr64 {
    uint16_t limit;
    uint64_t base;
} __attribute__((packed));

static idt_gate64 g_idt[CHIMERA_IDT_ENTRIES];
static idt_ptr64 g_idtr;
static volatile uint32_t g_initialized = 0;
static volatile uint32_t g_enabled = 0;
static volatile uint32_t g_exceptions = 0;
static volatile uint32_t g_irqs = 0;
static volatile uint32_t g_soft = 0;
static volatile uint32_t g_syscalls = 0;
static volatile uint32_t g_last = 0;

static void lidt(const idt_ptr64 *p) {
    __asm__ volatile("lidt (%0)" : : "r"(p) : "memory");
}

static bool is_exception(uint32_t v) {
    return v < 32u;
}

} // namespace

extern "C" int chimera_interrupt_init(void) {
    for (uint32_t i = 0; i < CHIMERA_IDT_ENTRIES; ++i) {
        const uint64_t a = (uint64_t)chimera_isr_table[i];
        idt_gate64 &g = g_idt[i];
        g.offset_low = (uint16_t)(a & 0xFFFFu);
        g.selector = 0x08u;
        g.ist = 0;
        /* Present 64-bit interrupt gate, DPL0. Software compatibility calls
         * are recognized by the dispatcher but are not exposed to ring 3 until
         * a TSS/user stack and validated user address space are installed. */
        g.type_attr = 0x8Eu;
        g.offset_mid = (uint16_t)((a >> 16) & 0xFFFFu);
        g.offset_high = (uint32_t)(a >> 32);
        g.reserved = 0;
    }
    g_idtr.limit = (uint16_t)(sizeof(g_idt) - 1u);
    g_idtr.base = (uint64_t)g_idt;
    lidt(&g_idtr);
    g_initialized = 1;
    g_enabled = 0;
    return 0;
}

extern "C" int chimera_interrupt_enable(void) {
    if (!g_initialized) return -1;
    __asm__ volatile("sti" ::: "memory");
    g_enabled = 1;
    return 0;
}

extern "C" int chimera_interrupt_disable(void) {
    __asm__ volatile("cli" ::: "memory");
    g_enabled = 0;
    return 0;
}

extern "C" int chimera_interrupt_get_snapshot(chimera_interrupt_snapshot *out) {
    if (!out) return -1;
    out->abi = CHIMERA_INTERRUPT_ABI;
    out->initialized = g_initialized;
    out->enabled = g_enabled;
    out->idt_entries = CHIMERA_IDT_ENTRIES;
    out->exception_count = g_exceptions;
    out->hardware_irq_count = g_irqs;
    out->software_irq_count = g_soft;
    out->syscall_count = g_syscalls;
    out->last_vector = g_last;
    return 0;
}

extern "C" void chimera_interrupt_dispatch(uint64_t vector, uint64_t frame) {
    (void)frame;
    if (vector > 255u) return;
    g_last = (uint32_t)vector;
    if (is_exception((uint32_t)vector)) ++g_exceptions;
    else if (vector >= 32u && vector != CHIMERA_SYSCALL_VECTOR) ++g_irqs;
    else ++g_soft;
    if (vector == CHIMERA_SYSCALL_VECTOR || vector == CHIMERA_WINDOWS_INT_VECTOR ||
        vector == CHIMERA_DOS_INT_VECTOR) {
        ++g_syscalls;
    }
    chimera_interrupt_identity identity{};
    chimera_compat_recognize_interrupt((uint32_t)vector, &identity);
}


namespace {
static volatile uint32_t user_timeout_ticks = 0;
static volatile uint32_t user_timeout_active = 0;
static inline void port_out8(uint16_t port, uint8_t value) {
    __asm__ volatile("outb %0, %1" : : "a"(value), "Nd"(port));
}
static inline void io_wait() { port_out8(0x80, 0); }
}

extern "C" int koronos_user_timeout_arm(uint32_t ticks) {
    if (ticks == 0) return -1;
    __asm__ volatile("cli" ::: "memory");
    if (chimera_interrupt_init() != 0) return -2;

    // Remap the legacy PIC to vectors 0x20..0x2f, then expose only IRQ0.
    port_out8(0x20, 0x11); io_wait();
    port_out8(0xA0, 0x11); io_wait();
    port_out8(0x21, 0x20); io_wait();
    port_out8(0xA1, 0x28); io_wait();
    port_out8(0x21, 0x04); io_wait();
    port_out8(0xA1, 0x02); io_wait();
    port_out8(0x21, 0x01); io_wait();
    port_out8(0xA1, 0x01); io_wait();

    // PIT channel 0, mode 3, approximately 100 Hz (1,193,182 / 11,932).
    const uint16_t divisor = 11932;
    port_out8(0x43, 0x36);
    port_out8(0x40, static_cast<uint8_t>(divisor & 0xffu));
    port_out8(0x40, static_cast<uint8_t>(divisor >> 8));

    user_timeout_ticks = ticks;
    user_timeout_active = 1;
    port_out8(0x21, 0xFE); // unmask IRQ0 only
    port_out8(0xA1, 0xFF); // mask all slave PIC IRQs
    return 0;
}

extern "C" void koronos_user_timeout_disarm(void) {
    __asm__ volatile("cli" ::: "memory");
    user_timeout_active = 0;
    user_timeout_ticks = 0;
    port_out8(0x21, 0xFF);
    port_out8(0xA1, 0xFF);
}

extern "C" int koronos_user_timeout_irq(void) {
    // Acknowledge IRQ0 before checking the deadline so the PIC can deliver
    // subsequent ticks while the user task is still within its time budget.
    port_out8(0x20, 0x20);
    if (!user_timeout_active) return 0;
    if (user_timeout_ticks > 0) --user_timeout_ticks;
    if (user_timeout_ticks == 0) {
        user_timeout_active = 0;
        return 1;
    }
    return 0;
}
