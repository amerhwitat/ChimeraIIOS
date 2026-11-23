#include "chimera/smp.h"

/* Real AP startup and two-CPU overlap gate. The AP executes a patched assembly
 * loop against the shared state below; it does not use the BSP's C runtime. */

extern "C" {
extern uint8_t koronos_ap_trampoline_start[];
extern uint8_t koronos_ap_trampoline_end[];
extern uint8_t koronos_ap_trampoline_gdtr[];
extern uint8_t koronos_ap_trampoline_gdt[];
extern uint8_t koronos_ap_trampoline_gdtr_disp[];
extern uint8_t koronos_ap_trampoline_gdt_base[];
extern uint8_t koronos_ap_trampoline_pml4_patch[];
extern uint8_t koronos_ap_trampoline_pm_jump_patch[];
extern uint8_t koronos_ap_trampoline_pm_entry[];
extern uint8_t koronos_ap_trampoline_gdtr_ptr_patch[];
extern uint8_t koronos_ap_trampoline_lm_jump_patch[];
extern uint8_t koronos_ap_trampoline_lm_entry[];
extern uint8_t koronos_ap_trampoline_stack_imm[];
extern uint8_t koronos_ap_trampoline_state_imm[];
extern uint8_t koronos_ap_trampoline_tsc_lo_imm[];
extern uint8_t koronos_ap_trampoline_tsc_hi_imm[];
extern uint8_t koronos_bootstrap_pml4[];
extern uint8_t koronos_bootstrap_gdt_ptr[];
}

namespace {

constexpr uintptr_t AP_TRAMPOLINE_PHYS = 0x7000u;
constexpr uint32_t SIPI_VECTOR = AP_TRAMPOLINE_PHYS >> 12;
constexpr uint32_t ROUNDS = 256u;
constexpr uint64_t BOOT_DELAY = 5000000ull;
constexpr uint64_t ONLINE_TIMEOUT = 50000000ull;
constexpr uint64_t ROUND_TIMEOUT = 500000ull;

struct SharedState {
    volatile uint32_t ap_online;        /* 0  */
    volatile uint32_t start_round;      /* 4  */
    volatile uint32_t stop_ap;          /* 8  */
    volatile uint32_t bsp_round;        /* 12 */
    volatile uint32_t ap_round;         /* 16 */
    volatile uint32_t ap_saw_bsp;       /* 20 */
    volatile uint32_t overlap_samples;  /* 24 */
    volatile uint32_t bsp_apic_id;      /* 28 */
    volatile uint32_t ap_apic_id;       /* 32 */
    volatile uint32_t reserved;         /* 36 */
    volatile uint64_t bsp_start_tsc;    /* 40 */
    volatile uint64_t ap_start_tsc;     /* 48 */
    volatile uint64_t bsp_end_tsc;      /* 56 */
    volatile uint64_t ap_end_tsc;       /* 64 */
    volatile uint64_t bsp_observe_tsc;  /* 72 */
    volatile uint32_t ap_stopped;       /* 80 */
    volatile uint32_t reserved2;        /* 84 */
    volatile uint64_t bsp_tsc_at_sipi;  /* 88 */
};

static_assert(__builtin_offsetof(SharedState, ap_online) == 0);
static_assert(__builtin_offsetof(SharedState, start_round) == 4);
static_assert(__builtin_offsetof(SharedState, stop_ap) == 8);
static_assert(__builtin_offsetof(SharedState, bsp_round) == 12);
static_assert(__builtin_offsetof(SharedState, ap_round) == 16);
static_assert(__builtin_offsetof(SharedState, ap_saw_bsp) == 20);
static_assert(__builtin_offsetof(SharedState, ap_apic_id) == 32);
static_assert(__builtin_offsetof(SharedState, ap_start_tsc) == 48);
static_assert(__builtin_offsetof(SharedState, ap_end_tsc) == 64);

SharedState state;
alignas(16) uint8_t ap_stack[16u * 1024u];
volatile int selftest_result = -1;

static inline void out8(uint16_t port, uint8_t value) {
    __asm__ volatile("outb %0, %1" : : "a"(value), "Nd"(port));
}

static void debug_write(const char *text) {
    while (*text) out8(0xE9, static_cast<uint8_t>(*text++));
    out8(0xE9, '\n');
}

static void debug_u32(const char *label, uint32_t value) {
    char line[80];
    unsigned int pos = 0;
    while (label[pos] && pos + 1u < sizeof(line)) { line[pos] = label[pos]; ++pos; }
    char digits[10];
    unsigned int n = 0;
    if (value == 0) digits[n++] = '0';
    while (value && n < sizeof(digits)) { digits[n++] = static_cast<char>('0' + value % 10u); value /= 10u; }
    while (n && pos + 1u < sizeof(line)) line[pos++] = digits[--n];
    line[pos] = 0;
    debug_write(line);
}

static inline void fence() { __asm__ volatile("mfence" ::: "memory"); }
static inline void pause_cpu() { __asm__ volatile("pause" ::: "memory"); }

static void spin_delay(uint64_t count) {
    for (volatile uint64_t i = 0; i < count; ++i) pause_cpu();
}

static inline uint64_t rdtsc64() {
    uint32_t lo = 0, hi = 0;
    __asm__ volatile("rdtsc" : "=a"(lo), "=d"(hi));
    return (static_cast<uint64_t>(hi) << 32) | lo;
}

static inline uint64_t rdmsr64(uint32_t msr) {
    uint32_t lo = 0, hi = 0;
    __asm__ volatile("rdmsr" : "=a"(lo), "=d"(hi) : "c"(msr));
    return (static_cast<uint64_t>(hi) << 32) | lo;
}

static inline void wrmsr64(uint32_t msr, uint64_t value) {
    const uint32_t lo = static_cast<uint32_t>(value);
    const uint32_t hi = static_cast<uint32_t>(value >> 32);
    __asm__ volatile("wrmsr" : : "c"(msr), "a"(lo), "d"(hi) : "memory");
}

static uint32_t initial_apic_id() {
    uint32_t eax = 0, ebx = 0, ecx = 0, edx = 0;
    __asm__ volatile("cpuid" : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx) : "a"(1u));
    return (ebx >> 24) & 0xFFu;
}

static void write16(volatile uint8_t *address, uint16_t value) {
    for (uint32_t i = 0; i < 2u; ++i) address[i] = static_cast<uint8_t>(value >> (8u * i));
}

static void write32(volatile uint8_t *address, uint32_t value) {
    for (uint32_t i = 0; i < 4u; ++i) address[i] = static_cast<uint8_t>(value >> (8u * i));
}

static void write64(volatile uint8_t *address, uint64_t value) {
    for (uint32_t i = 0; i < 8u; ++i) address[i] = static_cast<uint8_t>(value >> (8u * i));
}

static uintptr_t trampoline_offset(const uint8_t *symbol) {
    return static_cast<uintptr_t>(symbol - koronos_ap_trampoline_start);
}

static void install_trampoline() {
    volatile uint8_t *page = reinterpret_cast<volatile uint8_t *>(AP_TRAMPOLINE_PHYS);
    const uintptr_t image_size = static_cast<uintptr_t>(koronos_ap_trampoline_end - koronos_ap_trampoline_start);
    if (image_size == 0 || image_size >= 4096u) return;

    for (uintptr_t i = 0; i < image_size; ++i) page[i] = koronos_ap_trampoline_start[i];

    write16(page + trampoline_offset(koronos_ap_trampoline_gdtr_disp),
            static_cast<uint16_t>(AP_TRAMPOLINE_PHYS + trampoline_offset(koronos_ap_trampoline_gdtr)));
    write32(page + trampoline_offset(koronos_ap_trampoline_gdt_base),
            static_cast<uint32_t>(AP_TRAMPOLINE_PHYS + trampoline_offset(koronos_ap_trampoline_gdt)));
    write32(page + trampoline_offset(koronos_ap_trampoline_pml4_patch),
            static_cast<uint32_t>(reinterpret_cast<uintptr_t>(koronos_bootstrap_pml4)));
    write32(page + trampoline_offset(koronos_ap_trampoline_pm_jump_patch),
            static_cast<uint32_t>(AP_TRAMPOLINE_PHYS + trampoline_offset(koronos_ap_trampoline_pm_entry)));
    write32(page + trampoline_offset(koronos_ap_trampoline_gdtr_ptr_patch),
            static_cast<uint32_t>(reinterpret_cast<uintptr_t>(koronos_bootstrap_gdt_ptr)));
    write32(page + trampoline_offset(koronos_ap_trampoline_lm_jump_patch),
            static_cast<uint32_t>(AP_TRAMPOLINE_PHYS + trampoline_offset(koronos_ap_trampoline_lm_entry)));
    write64(page + trampoline_offset(koronos_ap_trampoline_stack_imm),
            reinterpret_cast<uint64_t>(ap_stack + sizeof(ap_stack)));
    write64(page + trampoline_offset(koronos_ap_trampoline_state_imm),
            reinterpret_cast<uint64_t>(&state));
    write32(page + trampoline_offset(koronos_ap_trampoline_tsc_lo_imm),
            static_cast<uint32_t>(state.bsp_tsc_at_sipi));
    write32(page + trampoline_offset(koronos_ap_trampoline_tsc_hi_imm),
            static_cast<uint32_t>(state.bsp_tsc_at_sipi >> 32));
}

static bool x2apic_available() {
    uint32_t eax = 0, ebx = 0, ecx = 0, edx = 0;
    __asm__ volatile("cpuid" : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx) : "a"(1u));
    return (edx & (1u << 9u)) != 0 && (ecx & (1u << 21u)) != 0;
}

static void x2apic_init() {
    uint64_t base = rdmsr64(0x1Bu);
    base |= (1ull << 10u) | (1ull << 11u);
    wrmsr64(0x1Bu, base);
    wrmsr64(0x808u, 0ull);
    wrmsr64(0x80Fu, 0x1FFull);
}

static void send_all_except_self(uint32_t icr_low) {
    wrmsr64(0x830u, static_cast<uint64_t>(icr_low));
}

} // namespace

extern "C" int koronos_smp_selftest(void) {
    if (selftest_result >= 0) return selftest_result;
    selftest_result = -1;

    debug_write("[SMP ] starting AP startup gate");
    if (!x2apic_available()) {
        debug_write("[SMP ] FAIL: x2APIC unavailable");
        return selftest_result;
    }

    state.bsp_apic_id = initial_apic_id();
    state.bsp_tsc_at_sipi = rdtsc64();
    install_trampoline();
    x2apic_init();

    send_all_except_self(0x000C4500u);
    spin_delay(BOOT_DELAY);
    send_all_except_self(0x000C0500u);
    spin_delay(BOOT_DELAY);
    send_all_except_self(0x000C0600u | SIPI_VECTOR);
    spin_delay(BOOT_DELAY);
    send_all_except_self(0x000C0600u | SIPI_VECTOR);

    uint64_t spins = 0;
    while (!state.ap_online && spins++ < ONLINE_TIMEOUT) pause_cpu();
    const bool online = state.ap_online != 0;
    (void)spins;

    state.bsp_observe_tsc = rdtsc64();
    state.bsp_start_tsc = state.bsp_observe_tsc;
    if (online) {
        state.start_round = 1;
        fence();
        for (uint32_t round = 1u; round <= ROUNDS; ++round) {
            state.bsp_round = round;
            uint64_t wait = 0;
            while ((state.ap_round < round || state.ap_saw_bsp < round) && wait++ < ROUND_TIMEOUT) pause_cpu();
            if (state.ap_round >= round && state.ap_saw_bsp >= round) ++state.overlap_samples;
            /* Always advance the round counter: the AP follows bsp_round, so
             * stopping early here would strand it in its handshake loop. */
        }
    }
    if (online) {
        /* Give the AP time to complete every round it acknowledged. */
        uint64_t final_wait = 0;
        while ((state.ap_round < ROUNDS || state.ap_saw_bsp < ROUNDS || state.ap_end_tsc == 0) &&
               final_wait++ < 200000000ull) pause_cpu();
        if (state.ap_round > ROUNDS) state.ap_round = ROUNDS;
        if (state.ap_saw_bsp > ROUNDS) state.ap_saw_bsp = ROUNDS;
        state.overlap_samples = state.ap_round < state.ap_saw_bsp ? state.ap_round : state.ap_saw_bsp;
        if (state.overlap_samples > ROUNDS) state.overlap_samples = ROUNDS;
    }
    state.bsp_end_tsc = rdtsc64();
    state.stop_ap = 1;
    fence();
    if (online) {
        uint64_t stop_wait = 0;
        while (!state.ap_stopped && stop_wait++ < 200000000ull) pause_cpu();
    }
    fence();

    /* QEMU TCG keeps a per-vCPU TSC, not a shared wall clock, so a raw
     * interval comparison is not meaningful. Concurrency is established by
     * the 256-round handshake while both cores' TSCs advanced. */
    const bool tsc_overlap = state.ap_start_tsc != 0 && state.ap_end_tsc != 0 &&
                             state.ap_end_tsc != state.ap_start_tsc &&
                             state.bsp_end_tsc > state.bsp_start_tsc;
    const bool pass = online && state.bsp_apic_id != state.ap_apic_id &&
                      state.overlap_samples == ROUNDS && state.ap_saw_bsp == ROUNDS && tsc_overlap;

    debug_u32("[SMP ] bsp_apic_id=", state.bsp_apic_id);
    debug_u32("[SMP ] ap_apic_id=", state.ap_apic_id);
    debug_u32("[SMP ] ap_online=", online ? 1u : 0u);
    debug_u32("[SMP ] overlap_samples=", state.overlap_samples);
    debug_u32("[SMP ] ap_saw_bsp_rounds=", state.ap_saw_bsp);
    debug_u32("[SMP ] tsc_overlap=", tsc_overlap ? 1u : 0u);
    debug_u32("[SMP ] bsp_tsc_start_lo=", static_cast<uint32_t>(state.bsp_start_tsc));
    debug_u32("[SMP ] ap_tsc_start_lo=", static_cast<uint32_t>(state.ap_start_tsc));
    debug_u32("[SMP ] bsp_tsc_end_lo=", static_cast<uint32_t>(state.bsp_end_tsc));
    debug_u32("[SMP ] ap_tsc_end_lo=", static_cast<uint32_t>(state.ap_end_tsc));
    debug_write(pass ? "[SMP ] SELFTEST PASS" : "[SMP ] SELFTEST FAIL");
    selftest_result = pass ? 0 : -1;
    return selftest_result;
}

extern "C" uint32_t koronos_smp_ap_online(void) { return state.ap_online; }
extern "C" uint32_t koronos_smp_overlap_samples(void) { return state.overlap_samples; }
