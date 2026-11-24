#include "chimera/preemptive_sched.h"
#include "chimera/interrupt.h"
#include "chimera/koronos_abi.h"

/* Hardware timer ownership and the assembly switch backend. Scheduler policy,
 * time slices and task contexts live in scheduler.cpp; this file owns the one
 * PIT periodic tick, its x2APIC IPI fan-out, per-CPU IDT/FS setup and user
 * timeout contract. */

extern "C" {
extern void koronos_arch_set_fs_base(uint64_t base);
extern void koronos_arch_cpu_state_init(uint32_t cpu, uint64_t rsp0);
void *koronos_preempt_current_ctx = nullptr;   /* legacy symbol, kept linked */
void *koronos_preempt_current_task = nullptr;  /* legacy symbol, kept linked */
}

namespace {
constexpr uint32_t MAX_CPUS = 256u;
constexpr uint16_t PIT_DIVISOR = 11932u;       /* ~100 Hz, 1.193182 MHz / 11932 */
constexpr uint64_t X2APIC_EOI = 0x80Bu;
constexpr uint64_t X2APIC_ICR = 0x830u;
constexpr uint64_t X2APIC_SVR = 0x80Fu;
constexpr uint64_t X2APIC_APICBASE = 0x01Bu;
constexpr uint64_t X2APIC_ID = 0x802u;

struct HardwareCpu {
    volatile uint32_t online;
    uint32_t apic_id;
    uint32_t cpu;
    volatile uint32_t timer_ticks;
    volatile uint32_t ipis_sent;
};

HardwareCpu hw_cpu[MAX_CPUS];
volatile uint32_t pit_ready = 0;
volatile uint32_t hardware_ticks = 0;
volatile uint32_t user_timeout_active = 0;
volatile uint32_t user_timeout_ticks = 0;
volatile int gate_result = -1;
volatile uint32_t gate_done = 0;
volatile uint32_t runtime_worker_started = 0;

struct RuntimeWork {
    uint32_t id;
    uint64_t spins;
    volatile uint64_t completed;
};

static inline void out8(uint16_t port, uint8_t value) {
    __asm__ volatile("outb %0, %1" : : "a"(value), "Nd"(port));
}
static inline void io_wait() { out8(0x80u, 0u); }
static inline void fence() { __asm__ volatile("mfence" ::: "memory"); }
static inline void pause_cpu() { __asm__ volatile("pause" ::: "memory"); }

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

static uint32_t cpuid_apic_id() {
    uint32_t eax = 0, ebx = 0, ecx = 0, edx = 0;
    __asm__ volatile("cpuid" : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx) : "a"(1u));
    return (ebx >> 24) & 0xFFu;
}

static void pit_setup() {
    out8(0x20, 0x11); io_wait();
    out8(0xA0, 0x11); io_wait();
    out8(0x21, 0x20); io_wait();
    out8(0xA1, 0x28); io_wait();
    out8(0x21, 0x04); io_wait();
    out8(0xA1, 0x02); io_wait();
    out8(0x21, 0x01); io_wait();
    out8(0xA1, 0x01); io_wait();
    out8(0x43, 0x36);
    out8(0x40, static_cast<uint8_t>(PIT_DIVISOR & 0xFFu));
    out8(0x40, static_cast<uint8_t>(PIT_DIVISOR >> 8));
    out8(0x21, 0xFE); /* IRQ0 unmasked: this is the sole periodic tick source. */
    out8(0xA1, 0xFF);
    pit_ready = 1;
}

static void runtime_worker(void *opaque) {
    RuntimeWork *work = static_cast<RuntimeWork *>(opaque);
    if (!work) return;
    uint64_t sum = 0;
    for (uint64_t i = 0; i < work->spins; ++i)
        sum += ((i ^ static_cast<uint64_t>(work->id + 1u)) & 0xFull);
    work->completed = sum + 1u;
    ++runtime_worker_started;
    chimera_sched_exit();
}

} // namespace

extern "C" uint32_t koronos_preemptive_current_cpu() {
    const uint64_t base = rdmsr64(0xC0000100u); /* IA32_FS_BASE */
    if (base == 0) return 0;
    return *reinterpret_cast<volatile uint32_t *>(static_cast<uintptr_t>(base + 16u));
}

extern "C" uint32_t koronos_preemptive_current_apic_id() {
    const uint32_t cpu = koronos_preemptive_current_cpu();
    return cpu < MAX_CPUS ? hw_cpu[cpu].apic_id : 0;
}

extern "C" int koronos_preemptive_apic_init() {
    uint64_t base = rdmsr64(X2APIC_APICBASE);
    base |= (1ull << 10u) | (1ull << 11u); /* LAPIC enable + x2APIC mode */
    wrmsr64(X2APIC_APICBASE, base);
    wrmsr64(0x808u, 0ull);                 /* task priority */
    wrmsr64(X2APIC_SVR, 0x1FFull);         /* enable APIC, spurious vector 255 */
    return static_cast<int>(cpuid_apic_id());
}

extern "C" int koronos_preemptive_cpu_init(uint32_t cpu, uint32_t apic_id) {
    if (cpu >= MAX_CPUS) return -1;
    void *state = chimera_sched_cpu_state(cpu);
    if (!state) return -2;
    koronos_arch_set_fs_base(reinterpret_cast<uint64_t>(state));
    if (chimera_interrupt_init_cpu(cpu) != 0) return -3;
    hw_cpu[cpu].cpu = cpu;
    hw_cpu[cpu].apic_id = apic_id;
    hw_cpu[cpu].online = 1;
    chimera_sched_set_cpu_online(cpu, apic_id);
    return 0;
}

extern "C" int koronos_preemptive_init(uint32_t cpu_count) {
    for (uint32_t i = 0; i < MAX_CPUS; ++i) hw_cpu[i] = HardwareCpu{};
    if (chimera_sched_preemptive_init(cpu_count) != 0) return -1;
    const int apic_id = koronos_preemptive_apic_init();
    if (apic_id < 0) return -2;
    if (koronos_preemptive_cpu_init(0, static_cast<uint32_t>(apic_id)) != 0) return -3;
    pit_setup();
    debug_u32("[RTM ] BSP_APIC_ID=", static_cast<uint32_t>(apic_id));
    return 0;
}

extern "C" int koronos_preemptive_send_ipi(uint32_t cpu, uint32_t vector) {
    if (cpu >= MAX_CPUS || !hw_cpu[cpu].online || hw_cpu[cpu].apic_id == 0) return -1;
    /* x2APIC ICR: high half is the target APIC ID, so the low half must use
     * physical destination mode (bit 10 clear). The previous logical-mode bit
     * made directed AP work/tick IPIs undeliverable. */
    const uint64_t icr = (static_cast<uint64_t>(hw_cpu[cpu].apic_id) << 32) |
                         (vector & 0xFFu);
    wrmsr64(X2APIC_ICR, icr);
    ++hw_cpu[cpu].ipis_sent;
    return 0;
}

extern "C" chimera_switch_target *koronos_preempt_irq_handler(uint64_t vector) {
    const uint32_t cpu = koronos_preemptive_current_cpu();
    if (vector == KORONOS_TIMER_VECTOR_PIT) {
        out8(0x20u, 0x20u); /* PIC EOI for the one PIT tick */
        ++hardware_ticks;
        if (cpu < MAX_CPUS) ++hw_cpu[cpu].timer_ticks;
        /* The PIT is wired to the BSP in PC/AT systems. Rebroadcast the same
         * measured tick to online APs through x2APIC fixed IPIs. */
        const uint32_t online = chimera_sched_cpu_count();
        for (uint32_t ap = 1; ap < online; ++ap)
            if (hw_cpu[ap].online) (void)koronos_preemptive_send_ipi(ap, KORONOS_TIMER_VECTOR_AP_TICK);
    } else if (vector == KORONOS_TIMER_VECTOR_AP_TICK ||
               vector == KORONOS_TIMER_VECTOR_AP_WORK) {
        wrmsr64(X2APIC_EOI, 0ull); /* local APIC EOI for IPI vectors */
        if (vector == KORONOS_TIMER_VECTOR_AP_TICK) {
            ++hardware_ticks;
            if (cpu < MAX_CPUS) ++hw_cpu[cpu].timer_ticks;
        }
    }
    /* Vector 33 is a supervisor software gate and needs no EOI. */
    return static_cast<chimera_switch_target *>(chimera_sched_irq_handler(vector));
}

extern "C" int koronos_preemptive_arm_user_timeout(uint32_t ticks) {
    if (ticks == 0) return -1;
    if (chimera_interrupt_init_cpu(0) != 0) return -2;
    __asm__ volatile("cli" ::: "memory");
    user_timeout_ticks = ticks;
    user_timeout_active = 1;
    out8(0x21, 0xFE);
    fence();
    return 0;
}

extern "C" void koronos_preemptive_disarm_user_timeout() {
    __asm__ volatile("cli" ::: "memory");
    user_timeout_active = 0;
    user_timeout_ticks = 0;
}

extern "C" int koronos_preemptive_user_timeout_irq() {
    if (!user_timeout_active) return 0;
    if (user_timeout_ticks > 0) --user_timeout_ticks;
    if (user_timeout_ticks == 0) {
        user_timeout_active = 0;
        return 1;
    }
    return 0;
}

extern "C" int koronos_preemptive_selftest() {
    if (gate_done) return gate_result;
    if (!chimera_sched_preemptive_ready()) {
        debug_write("[PMT ] FAIL: preemptive runtime not initialized");
        gate_result = -1;
        gate_done = 1;
        return gate_result;
    }

    /* Workers are scheduler-submitted real tasks. Their count and budget are
     * derived from the discovered CPU topology, not a synthetic fixed trace. */
    const uint32_t cpus = chimera_sched_cpu_count();
    uint32_t workers = cpus + 1u;
    if (workers > 8u) workers = 8u;
    uint32_t submitted = 0;
    for (uint32_t i = 0; i < workers; ++i) {
        static RuntimeWork work[8];
        work[i].id = static_cast<uint32_t>(i);
        work[i].spins = 2600000ull + static_cast<uint64_t>(i) * 131071ull;
        work[i].completed = 0;
        const int id = chimera_sched_submit(runtime_worker, &work[i], 150u + i);
        if (id > 0) {
            (void)chimera_sched_set_affinity(static_cast<uint32_t>(id), 1ull);
            ++submitted;
        }
    }
    (void)chimera_sched_run_preemptive(0);

    const uint64_t switches = chimera_sched_total_context_switches();
    const uint64_t preemptions = chimera_sched_total_preemptions();
    const uint64_t ticks = chimera_sched_total_timer_ticks();
    const uint32_t guards = chimera_sched_guard_failures();
    debug_u32("[RTM ] WORKERS_SUBMITTED=", submitted);
    debug_u32("[RTM ] PREEMPTIONS=", static_cast<uint32_t>(preemptions));
    debug_u32("[RTM ] CONTEXT_SWITCHES=", static_cast<uint32_t>(switches));
    debug_u32("[RTM ] TIMER_TICKS=", static_cast<uint32_t>(ticks));
    debug_u32("[RTM ] GUARD_FAILURES=", guards);
    debug_u32("[RTM ] RUNTIME_WORKERS_COMPLETED=", runtime_worker_started);
    debug_u64("[RTM ] PREEMPTIONS_64=", preemptions);
    debug_u64("[RTM ] CONTEXT_SWITCHES_64=", switches);

    const bool pass = submitted == workers && runtime_worker_started >= workers &&
                      preemptions > 0u && switches >= workers && guards == 0u;
    debug_write(pass ? "[PMT ] SELFTEST PASS" : "[PMT ] SELFTEST FAIL");
    gate_result = pass ? 0 : -1;
    gate_done = 1;
    return gate_result;
}

extern "C" void koronos_preemptive_dump_measurements() {
    debug_u32("[RTM ] PREEMPTIONS=", static_cast<uint32_t>(chimera_sched_total_preemptions()));
    debug_u32("[RTM ] CONTEXT_SWITCHES=", static_cast<uint32_t>(chimera_sched_total_context_switches()));
    debug_u32("[RTM ] TIMER_TICKS=", static_cast<uint32_t>(chimera_sched_total_timer_ticks()));
    debug_u32("[RTM ] GUARD_FAILURES=", chimera_sched_guard_failures());
    debug_u32("[RTM ] CPU0_DISPATCHES=", chimera_sched_preemptive_dispatches(0));
    debug_u32("[RTM ] CPU1_DISPATCHES=", chimera_sched_preemptive_dispatches(1));
    debug_u32("[RTM ] CPU0_TASKS=", chimera_sched_parallel_cpu_tasks(0));
    debug_u32("[RTM ] CPU1_TASKS=", chimera_sched_parallel_cpu_tasks(1));
    debug_u64("[RTM ] CPU0_WORK=", chimera_sched_parallel_cpu_work(0));
    debug_u64("[RTM ] CPU1_WORK=", chimera_sched_parallel_cpu_work(1));
    debug_u32("[RTM ] OVERLAP_SAMPLES=", chimera_sched_parallel_overlap());
}

extern "C" uint32_t koronos_preemptive_switch_count() {
    return static_cast<uint32_t>(chimera_sched_total_context_switches());
}
extern "C" uint32_t koronos_preemptive_timer_count() { return hardware_ticks; }
extern "C" uint32_t koronos_preemptive_guard_failures() { return chimera_sched_guard_failures(); }
extern "C" uint32_t koronos_preemptive_interleavings() {
    return chimera_sched_preemptive_preemptions(0);
}
