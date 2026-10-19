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
        /* INT 0x80 is the one DPL3 software gate. Its handler validates the
         * hardware-saved CS.RPL and active process CR3 before emitting evidence.
         * All other interrupt gates remain supervisor-only. */
        g.type_attr = (i == CHIMERA_SYSCALL_VECTOR) ? 0xEEu : 0x8Eu;
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

extern "C" uint32_t koronos_target_note_user_syscall(uint64_t user_rip, uint64_t user_cs);
extern "C" void koronos_target_log(const char *message);

extern "C" void chimera_interrupt_dispatch(uint64_t vector, uint64_t frame) {
    static volatile uint32_t first_transition_exception = 0;
    if (vector > 255u) return;
    /* Emit one address-bearing record for the first transition exception.
     * Repeatedly IRET'ing to the same faulting RIP must not flood debugcon. */
    if ((vector == 6u || vector == 13u || vector == 14u) &&
        __sync_bool_compare_and_swap(&first_transition_exception, 0u, 1u)) {
        const uint64_t *saved = reinterpret_cast<const uint64_t *>(static_cast<uintptr_t>(frame));
        const uint64_t rip = saved ? saved[16] : 0u;
        const char *kind = vector == 6u ? "[EXC] #UD RIP=0x" :
                           (vector == 13u ? "[EXC] #GP RIP=0x" : "[EXC] #PF RIP=0x");
        char message[64]; size_t pos = 0;
        while (kind[pos] && pos < sizeof(message)-1u) { message[pos] = kind[pos]; ++pos; }
        for (int shift = 60; shift >= 0 && pos < sizeof(message)-1u; shift -= 4)
            message[pos++] = "0123456789ABCDEF"[(rip >> shift) & 0xFu];
        message[pos] = 0;
        koronos_target_log(message);
    }
    g_last = (uint32_t)vector;
    if (is_exception((uint32_t)vector)) ++g_exceptions;
    else if (vector >= 32u && vector != CHIMERA_SYSCALL_VECTOR) ++g_irqs;
    else ++g_soft;
    if (vector == CHIMERA_SYSCALL_VECTOR || vector == CHIMERA_WINDOWS_INT_VECTOR ||
        vector == CHIMERA_DOS_INT_VECTOR) {
        ++g_syscalls;
    }
    if (vector == CHIMERA_SYSCALL_VECTOR && frame) {
        /* interrupts.asm saves 15 GPRs, then vector, then the hardware frame:
         * frame[16] is RIP and frame[17] is CS. INT 0x80's IDT gate is DPL3;
         * still check the CPU-saved RPL explicitly before acknowledging. */
        const uint64_t *saved = reinterpret_cast<const uint64_t *>(static_cast<uintptr_t>(frame));
        (void)koronos_target_note_user_syscall(saved[16], saved[17]);
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
