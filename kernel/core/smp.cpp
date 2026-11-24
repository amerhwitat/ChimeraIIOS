#include "chimera/smp.h"
#include "chimera/scheduler.h"
#include "chimera/preemptive_sched.h"

/* Real x2APIC INIT/SIPI startup followed by a resident per-CPU C scheduler
 * loop. The AP executes scheduler-submitted work, reports its own APIC ID and
 * measured work count, and remains online for later dispatch. */

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
extern uint8_t koronos_ap_trampoline_lm_jump_patch[];
extern uint8_t koronos_ap_trampoline_lm_entry[];
extern uint8_t koronos_ap_trampoline_stack_base_imm[];
extern uint8_t koronos_ap_trampoline_state_imm[];
extern uint8_t koronos_ap_trampoline_entry_imm[];
extern uint8_t koronos_bootstrap_pml4[];
extern void koronos_arch_cpu_state_init(uint32_t cpu, uint64_t rsp0);
void koronos_ap_cpu_entry(uint32_t apic_id, void *opaque);
}

namespace {
constexpr uintptr_t AP_TRAMPOLINE_PHYS = 0x7000u;
constexpr uint32_t SIPI_VECTOR = AP_TRAMPOLINE_PHYS >> 12;
constexpr uint32_t MAX_CPUS = 256u;
constexpr uint32_t AP_STACK_BYTES = 64u * 1024u;
constexpr uint64_t BOOT_DELAY = 5000000ull;
constexpr uint64_t ONLINE_TIMEOUT = 500000000ull;

struct SharedState {
    volatile uint32_t bsp_apic_id;
    volatile uint32_t ap_apic_id;
    volatile uint32_t ap_online;
    volatile uint32_t ap_cpu_slot;
    volatile uint32_t parallel_return;
    volatile uint32_t overlap_samples;
    volatile uint32_t reserved0;
    volatile uint32_t reserved1;
    volatile uint64_t ap_entry_tsc;
    volatile uint64_t bsp_start_tsc;
    volatile uint64_t ap_start_tsc;
    volatile uint64_t bsp_end_tsc;
    volatile uint64_t ap_end_tsc;
};

alignas(64) uint8_t ap_stack_area[MAX_CPUS][AP_STACK_BYTES];
SharedState state;
volatile uint32_t ap_slot_apic[MAX_CPUS];
volatile uint32_t online_cpu_mask = 1u;
volatile int smp_result = -1;

static inline void out8(uint16_t port, uint8_t value) {
    __asm__ volatile("outb %0, %1" : : "a"(value), "Nd"(port));
}
static inline void pause_cpu() { __asm__ volatile("pause" ::: "memory"); }
static inline void fence() { __asm__ volatile("mfence" ::: "memory"); }

static void debug_write(const char *text) {
    while (*text) out8(0xE9u, static_cast<uint8_t>(*text++));
    out8(0xE9u, '\n');
}

static void debug_u32(const char *label, uint32_t value) {
    char line[96];
    uint32_t pos = 0;
    while (label[pos] && pos + 1u < sizeof(line)) { line[pos] = label[pos]; ++pos; }
    char digits[10];
    uint32_t n = 0;
    if (value == 0) digits[n++] = '0';
    while (value && n < sizeof(digits)) { digits[n++] = static_cast<char>('0' + value % 10u); value /= 10u; }
    while (n && pos + 1u < sizeof(line)) line[pos++] = digits[--n];
    line[pos] = 0;
    debug_write(line);
}

static void debug_u64(const char *label, uint64_t value) {
    char line[96];
    uint32_t pos = 0;
    while (label[pos] && pos + 1u < sizeof(line)) { line[pos] = label[pos]; ++pos; }
    char digits[20];
    uint32_t n = 0;
    if (value == 0) digits[n++] = '0';
    while (value && n < sizeof(digits)) { digits[n++] = static_cast<char>('0' + value % 10u); value /= 10u; }
    while (n && pos + 1u < sizeof(line)) line[pos++] = digits[--n];
    line[pos] = 0;
    debug_write(line);
}

static void append_u32(char *line, uint32_t pos, uint32_t value, uint32_t capacity) {
    char digits[10];
    uint32_t n = 0;
    if (value == 0) digits[n++] = '0';
    while (value && n < sizeof(digits)) { digits[n++] = static_cast<char>('0' + value % 10u); value /= 10u; }
    while (n && pos + 1u < capacity) line[pos++] = digits[--n];
    line[pos] = 0;
}

static void debug_ap_cpu_ids() {
    char line[128];
    const char label[] = "[SMP ] AP_CPU_IDS=";
    uint32_t pos = 0;
    while (label[pos] && pos + 1u < sizeof(line)) { line[pos] = label[pos]; ++pos; }
    bool first = true;
    for (uint32_t cpu = 1; cpu < MAX_CPUS; ++cpu) {
        if (!chimera_sched_cpu_online(cpu)) continue;
        if (!first && pos + 1u < sizeof(line)) line[pos++] = ',';
        append_u32(line, pos, cpu, sizeof(line));
        while (pos < sizeof(line) && line[pos]) ++pos;
        first = false;
    }
    if (first) line[pos ? pos : 0] = 0;
    debug_write(line);
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

static void spin_delay(uint64_t count) {
    for (volatile uint64_t i = 0; i < count; ++i) pause_cpu();
}

static bool x2apic_available() {
    uint32_t eax = 0, ebx = 0, ecx = 0, edx = 0;
    __asm__ volatile("cpuid" : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx) : "a"(1u));
    return (edx & (1u << 9u)) != 0 && (ecx & (1u << 21u)) != 0;
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
    write32(page + trampoline_offset(koronos_ap_trampoline_lm_jump_patch),
            static_cast<uint32_t>(AP_TRAMPOLINE_PHYS + trampoline_offset(koronos_ap_trampoline_lm_entry)));
    write64(page + trampoline_offset(koronos_ap_trampoline_stack_base_imm),
            reinterpret_cast<uint64_t>(&ap_stack_area[1][AP_STACK_BYTES]));
    write64(page + trampoline_offset(koronos_ap_trampoline_state_imm),
            reinterpret_cast<uint64_t>(&state));
    write64(page + trampoline_offset(koronos_ap_trampoline_entry_imm),
            reinterpret_cast<uint64_t>(&koronos_ap_cpu_entry));
}

static void send_all_except_self(uint32_t icr_low) {
    wrmsr64(0x830u, static_cast<uint64_t>(icr_low));
}

static uint32_t allocate_ap_slot(uint32_t apic_id) {
    for (uint32_t slot = 1; slot < MAX_CPUS; ++slot) {
        if (__sync_bool_compare_and_swap(&ap_slot_apic[slot], 0u, apic_id ? apic_id : 1u)) {
            return slot;
        }
    }
    return 0;
}

} // namespace

extern "C" void koronos_ap_cpu_entry(uint32_t apic_id, void *opaque) {
    const int detected_apic = koronos_preemptive_apic_init();
    if (detected_apic > 0) apic_id = static_cast<uint32_t>(detected_apic);
    SharedState *shared = static_cast<SharedState *>(opaque);
    if (!shared || apic_id == 0 || apic_id >= MAX_CPUS) {
        for (;;) __asm__ volatile("hlt");
    }
    const uint32_t slot = allocate_ap_slot(apic_id);
    if (slot == 0) {
        for (;;) __asm__ volatile("hlt");
    }
    const uint64_t stack_top = reinterpret_cast<uint64_t>(&ap_stack_area[slot][0]) + AP_STACK_BYTES;
    koronos_arch_cpu_state_init(slot, stack_top);
    if (koronos_preemptive_cpu_init(slot, apic_id) != 0) {
        for (;;) __asm__ volatile("hlt");
    }
    /* The SIPI stub enters with IF cleared. Enable the locally initialized IDT
     * before joining the scheduler so timer/work IPIs can dispatch real tasks. */
    __asm__ volatile("sti" ::: "memory");

    shared->ap_apic_id = apic_id;
    shared->ap_cpu_slot = slot;
    shared->ap_entry_tsc = rdtsc64();
    __sync_fetch_and_or(&online_cpu_mask, 1u << (slot < 32u ? slot : 31u));
    shared->ap_online = 1;
    fence();
    debug_u32("[SMP ] AP_CPU_ONLINE cpu=", slot);
    debug_u32("[SMP ] AP_APIC_ID=", apic_id);

    /* Resident per-CPU scheduler loop. The core never parks after startup. */
    for (;;) {
        (void)chimera_sched_run_preemptive(slot);
        pause_cpu();
    }
}

extern "C" int koronos_smp_selftest() {
    if (smp_result >= 0) return smp_result;
    smp_result = -1;
    debug_write("[SMP ] starting resident AP runtime gate");
    if (!x2apic_available()) {
        debug_write("[SMP ] FAIL: x2APIC unavailable");
        return smp_result;
    }

    state.bsp_apic_id = initial_apic_id();
    install_trampoline();
    send_all_except_self(0x000C4500u); /* INIT, all except self */
    spin_delay(BOOT_DELAY);
    send_all_except_self(0x000C0500u); /* SIPI, all except self */
    spin_delay(BOOT_DELAY);
    send_all_except_self(0x000C0600u | SIPI_VECTOR);
    spin_delay(BOOT_DELAY);
    send_all_except_self(0x000C0600u | SIPI_VECTOR);

    uint64_t spins = 0;
    while (!state.ap_online && spins++ < ONLINE_TIMEOUT) pause_cpu();
    const bool online = state.ap_online != 0 && state.ap_cpu_slot != 0;

    uint32_t parallel_return = 0;
    if (online) {
        const uint32_t cpus = chimera_sched_cpu_count();
        parallel_return = chimera_sched_run_parallel(state.ap_cpu_slot,
                                                     cpus > state.ap_cpu_slot ? cpus - state.ap_cpu_slot : 0u);
        state.parallel_return = parallel_return;
        state.overlap_samples = chimera_sched_parallel_overlap();
        uint64_t bsp_start = 0, ap_start = 0, bsp_end = 0, ap_end = 0;
        chimera_sched_parallel_timestamps(&bsp_start, &ap_start, &bsp_end, &ap_end);
        state.bsp_start_tsc = bsp_start;
        state.ap_start_tsc = ap_start;
        state.bsp_end_tsc = bsp_end;
        state.ap_end_tsc = ap_end;
    }
    fence();

    const uint32_t cpu0_tasks = chimera_sched_parallel_cpu_tasks(0);
    const uint32_t cpu1_tasks = chimera_sched_parallel_cpu_tasks(1);
    const uint64_t cpu0_work = chimera_sched_parallel_cpu_work(0);
    const uint64_t cpu1_work = chimera_sched_parallel_cpu_work(1);
    const bool work = cpu0_tasks > 0u && cpu1_tasks > 0u && cpu0_work > 0u && cpu1_work > 0u;
    const bool timestamps = state.bsp_start_tsc != 0 && state.bsp_end_tsc > state.bsp_start_tsc &&
                            state.ap_start_tsc != 0 && state.ap_end_tsc > state.ap_start_tsc;
    const bool overlap = state.overlap_samples > 0u;
    const bool pass = online && state.bsp_apic_id != state.ap_apic_id &&
                      parallel_return >= 1u && work && timestamps && overlap;

    debug_u32("[SMP ] BSP_APIC_ID=", state.bsp_apic_id);
    debug_u32("[SMP ] AP_APIC_ID=", state.ap_apic_id);
    debug_ap_cpu_ids();
    debug_u32("[SMP ] AP_ONLINE=", online ? 1u : 0u);
    debug_u32("[SMP ] PARALLEL_RETURN=", parallel_return);
    debug_u32("[SMP ] CPU0_TASKS=", cpu0_tasks);
    debug_u32("[SMP ] CPU1_TASKS=", cpu1_tasks);
    debug_u64("[SMP ] CPU0_WORK=", cpu0_work);
    debug_u64("[SMP ] CPU1_WORK=", cpu1_work);
    debug_u32("[SMP ] OVERLAP_SAMPLES=", state.overlap_samples);
    debug_u32("[SMP ] TSC_OVERLAP=", timestamps ? 1u : 0u);
    debug_u64("[SMP ] BSP_START_TSC=", state.bsp_start_tsc);
    debug_u64("[SMP ] AP_START_TSC=", state.ap_start_tsc);
    debug_u64("[SMP ] BSP_END_TSC=", state.bsp_end_tsc);
    debug_u64("[SMP ] AP_END_TSC=", state.ap_end_tsc);
    debug_write(pass ? "[SMP ] SELFTEST PASS" : "[SMP ] SELFTEST FAIL");
    smp_result = pass ? 0 : -1;
    return smp_result;
}

extern "C" uint32_t koronos_smp_ap_online() { return state.ap_online; }
extern "C" uint32_t koronos_smp_overlap_samples() { return state.overlap_samples; }
extern "C" uint32_t koronos_smp_online_cpu_count() {
    uint32_t n = 0;
    for (uint32_t cpu = 0; cpu < MAX_CPUS; ++cpu)
        if (chimera_sched_cpu_online(cpu)) ++n;
    return n;
}

extern "C" void koronos_smp_dump_measurements() {
    debug_u32("[RTM ] CPU_ID_COUNT=", koronos_smp_online_cpu_count());
    debug_u32("[RTM ] AP_ONLINE=", state.ap_online);
    debug_u32("[RTM ] AP_CPU_SLOT=", state.ap_cpu_slot);
    debug_u32("[RTM ] BSP_APIC_ID=", state.bsp_apic_id);
    debug_u32("[RTM ] AP_APIC_ID=", state.ap_apic_id);
    debug_u32("[RTM ] PARALLEL_RETURN=", state.parallel_return);
    debug_u32("[RTM ] CPU0_TASKS=", chimera_sched_parallel_cpu_tasks(0));
    debug_u32("[RTM ] CPU1_TASKS=", chimera_sched_parallel_cpu_tasks(1));
    debug_u64("[RTM ] CPU0_WORK=", chimera_sched_parallel_cpu_work(0));
    debug_u64("[RTM ] CPU1_WORK=", chimera_sched_parallel_cpu_work(1));
    debug_u32("[RTM ] OVERLAP_SAMPLES=", chimera_sched_parallel_overlap());
    debug_ap_cpu_ids();
}
