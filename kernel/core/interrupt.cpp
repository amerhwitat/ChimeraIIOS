#include "chimera/interrupt.h"
#include "chimera/compat.h"
#include "chimera/user_mode.h"

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
        /* Ring 0 by default. Only the bounded bootstrap write syscall at
         * vector 0x80 is callable from ring 3 (DPL3). */
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

extern "C" void chimera_interrupt_dispatch(uint64_t vector, uint64_t frame) {
    if (vector > 255u) return;
    g_last = (uint32_t)vector;
    if (is_exception((uint32_t)vector)) ++g_exceptions;
    else if (vector >= 32u && vector != CHIMERA_SYSCALL_VECTOR) ++g_irqs;
    else ++g_soft;
    if (vector == CHIMERA_SYSCALL_VECTOR || vector == CHIMERA_WINDOWS_INT_VECTOR ||
        vector == CHIMERA_DOS_INT_VECTOR) ++g_syscalls;

    /*
     * Minimal, bounded ring-3 ABI used by the bootstrap init and diagnostics:
     * RAX=1, RDI=user pointer, RSI=byte count. This is deliberately not a
     * claim of POSIX syscall compatibility. Only the dedicated user range and
     * a small maximum length are accepted; output is emitted from ring 0.
     */
    if (vector == CHIMERA_SYSCALL_VECTOR && frame) {
        uint64_t *regs = (uint64_t *)(uintptr_t)frame;
        const uint64_t number = regs[14]; // saved RAX
        const uint64_t ptr = regs[8];     // saved RDI
        const uint64_t len = regs[9];     // saved RSI
        if (number == 1u && chimera_x86_64_user_range_valid(ptr,len)) {
            const char *message = (const char *)(uintptr_t)ptr;
            for (uint64_t n = 0; n < len; ++n) {
                const uint8_t c = (uint8_t)message[n];
                __asm__ volatile("outb %0, $0xE9" : : "a"(c));
            }
            regs[14] = len;
        } else {
            regs[14] = UINT64_MAX;
        }
        return;
    }

    chimera_interrupt_identity identity{};
    chimera_compat_recognize_interrupt((uint32_t)vector, &identity);
}
