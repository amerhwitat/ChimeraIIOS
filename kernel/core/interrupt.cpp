#include <stddef.h>
#include "chimera/interrupt.h"
#include "chimera/compat.h"
#include "chimera/preemptive_sched.h"

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

constexpr uint32_t MAX_IDT_CPUS = 256u;
static idt_gate64 g_idt[MAX_IDT_CPUS][CHIMERA_IDT_ENTRIES];
static idt_ptr64 g_idtr[MAX_IDT_CPUS];
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

extern "C" int chimera_interrupt_init_cpu(uint32_t cpu) {
    if (cpu >= MAX_IDT_CPUS) return -1;
    for (uint32_t i = 0; i < CHIMERA_IDT_ENTRIES; ++i) {
        const uint64_t a = (uint64_t)chimera_isr_table[i];
        idt_gate64 &g = g_idt[cpu][i];
        g.offset_low = (uint16_t)(a & 0xFFFFu);
        g.selector = 0x08u;
        g.ist = 0;
        g.type_attr = (i == CHIMERA_SYSCALL_VECTOR) ? 0xEEu : 0x8Eu;
        g.offset_mid = (uint16_t)((a >> 16) & 0xFFFFu);
        g.offset_high = (uint32_t)(a >> 32);
        g.reserved = 0;
    }
    g_idtr[cpu].limit = (uint16_t)(sizeof(g_idt[0]) - 1u);
    g_idtr[cpu].base = (uint64_t)g_idt[cpu];
    lidt(&g_idtr[cpu]);
    g_initialized = 1;
    return 0;
}

extern "C" int chimera_interrupt_init(void) { return chimera_interrupt_init_cpu(0); }

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
    if ((vector == 6u || vector == 13u || vector == 14u) &&
        __sync_bool_compare_and_swap(&first_transition_exception, 0u, 1u)) {
        const uint64_t *saved = reinterpret_cast<const uint64_t *>(static_cast<uintptr_t>(frame));
        const uint64_t rip = saved ? saved[16] : 0u;
        const char *kind = vector == 6u ? "[EXC] #UD RIP=0x" :
                           (vector == 13u ? "[EXC] #GP RIP=0x" : "[EXC] #PF RIP=0x");
        char message[64]; unsigned int pos = 0;
        while (pos < sizeof(message)-1u && kind[pos]) { message[pos] = kind[pos]; ++pos; }
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
        const uint64_t *saved = reinterpret_cast<const uint64_t *>(static_cast<uintptr_t>(frame));
        (void)koronos_target_note_user_syscall(saved[16], saved[17]);
    }
    chimera_interrupt_identity identity{};
    chimera_compat_recognize_interrupt((uint32_t)vector, &identity);
}

/* User-process deadline ownership moved to the unified PIT/timer backend. */
extern "C" int koronos_user_timeout_arm(uint32_t ticks) {
    return koronos_preemptive_arm_user_timeout(ticks);
}
extern "C" void koronos_user_timeout_disarm(void) {
    koronos_preemptive_disarm_user_timeout();
}
extern "C" int koronos_user_timeout_irq(void) {
    return koronos_preemptive_user_timeout_irq();
}
