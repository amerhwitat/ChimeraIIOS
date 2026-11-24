#if defined(_MSC_VER)
#include <intrin.h>
#ifndef __sync_lock_test_and_set
#define __sync_lock_test_and_set(ptr, value) _InterlockedExchange(reinterpret_cast<volatile long *>(ptr), static_cast<long>(value))
#define __sync_lock_release(ptr) ((void)_InterlockedExchange(reinterpret_cast<volatile long *>(ptr), 0L))
#endif
#endif
#include "chimera/scheduler.h"
#include "chimera/preemptive_sched.h"

extern "C" void koronos_context_trampoline(void);
extern "C" void chimera_sched_task_entry(void *);
extern "C" void koronos_preempt_yield(void);

namespace {
constexpr uint32_t MAX_CPUS = 256u;
constexpr uint32_t MAX_TASKS = 256u;
constexpr uint32_t TASK_STACK_BYTES = 16u * 1024u;
constexpr uint32_t DEFAULT_SLICE_TICKS = 3u;
enum PendingAction : uint8_t { ACTION_NONE = 0, ACTION_YIELD = 1, ACTION_BLOCK = 2, ACTION_EXIT = 3 };

struct Context {
    uint64_t rsp;
    uint64_t cr3;
};
static_assert(sizeof(Context) == 16u, "asm expects a 16-byte context");

struct Task {
    chimera_task_fn fn;
    void *arg;
    chimera_task_info info;
    uint32_t round_seen;
    uint8_t pending_action;
    uint8_t reserved[3];
    uint64_t entry_count;
    uint64_t guard_low[8];
    Context ctx;
    alignas(16) uint8_t stack[TASK_STACK_BYTES];
    uint64_t guard_high[8];
};

/* FS base points at CpuState. Offset 0 is read directly by interrupts.asm. */
struct CpuState {
    Context *current_ctx;
    uint64_t current_cr3;
    uint32_t cpu;
    Task *current_task;
    uint32_t online;
    uint32_t apic_id;
    uint32_t work_count;
    volatile uint32_t in_loop;
    volatile uint32_t dispatched;
    volatile uint32_t switches;
    volatile uint32_t ticks;
    volatile uint32_t preemptions;
    volatile uint32_t guard_failures;
    Context idle_ctx;
    chimera_switch_target target;
};
static_assert(__builtin_offsetof(CpuState, current_ctx) == 0u, "FS ctx offset");
static_assert(__builtin_offsetof(CpuState, cpu) == 16u, "FS cpu offset");

struct ParallelWork {
    chimera_task_fn fn;
    uint32_t cpu;
    uint32_t apic_id;
    uint64_t spins;
    volatile uint64_t counted;
    volatile uint32_t done;
    chimera_task_info info;
};

struct ParallelEvidence {
    volatile uint32_t active_mask;
    volatile uint32_t done_mask;
    volatile uint32_t expected_mask;
    volatile uint32_t overlap_samples;
    volatile uint64_t cpu_work[MAX_CPUS];
    volatile uint32_t cpu_tasks[MAX_CPUS];
    volatile uint64_t bsp_start_tsc;
    volatile uint64_t ap_start_tsc;
    volatile uint64_t bsp_end_tsc;
    volatile uint64_t ap_end_tsc;
};

Task tasks[MAX_TASKS];
CpuState cpu_state[MAX_CPUS];
ParallelWork parallel_work[MAX_CPUS];
ParallelEvidence evidence;
volatile int32_t current_index[MAX_CPUS];
volatile uint32_t lock_word = 0;
volatile uint32_t parallel_lock = 0;
uint32_t task_count = 0;
uint32_t next_id = 1;
uint32_t rr = 0;
uint32_t dispatch_round = 1;
uint32_t cpu_count = 1;
uint64_t kernel_cr3 = 0;
volatile uint32_t preemptive_ready = 0;
volatile uint64_t total_switches = 0;
volatile uint64_t total_preemptions = 0;
volatile uint64_t total_ticks = 0;
volatile uint32_t guard_failures_total = 0;


static inline void lock() { while (__sync_lock_test_and_set(&lock_word, 1u)) { } }
static inline void unlock() { __sync_lock_release(&lock_word); }
static inline void parallel_lock_acquire() { while (__sync_lock_test_and_set(&parallel_lock, 1u)) { } }
static inline void parallel_lock_release() { __sync_lock_release(&parallel_lock); }
static inline void fence() { __asm__ volatile("mfence" ::: "memory"); }
static inline void pause_cpu() { __asm__ volatile("pause" ::: "memory"); }

static inline uint64_t rdtsc64() {
    uint32_t lo = 0, hi = 0;
    __asm__ volatile("rdtsc" : "=a"(lo), "=d"(hi));
    return (static_cast<uint64_t>(hi) << 32) | lo;
}

static bool cpu_allowed(const chimera_task_info &info, uint32_t cpu) {
    if (cpu >= cpu_count) return false;
    if (info.affinity_mask == 0) return true;
    if (cpu >= 64u) return false;
    return (info.affinity_mask & (1ull << cpu)) != 0;
}

static int32_t pick_next_locked(uint32_t cpu) {
    if (task_count == 0) return -1;
    int32_t best = -1;
    uint32_t best_priority = 0;
    const uint32_t start = rr % task_count;
    bool found_unseen = false;
    for (uint32_t offset = 0; offset < task_count; ++offset) {
        const uint32_t i = (start + offset) % task_count;
        const chimera_task_info &info = tasks[i].info;
        if (info.state != CHIMERA_TASK_READY || !cpu_allowed(info, cpu)) continue;
        if (tasks[i].round_seen == dispatch_round) continue;
        found_unseen = true;
        if (best < 0 || info.priority > best_priority) {
            best = static_cast<int32_t>(i);
            best_priority = info.priority;
        }
    }
    if (!found_unseen) {
        ++dispatch_round;
        if (dispatch_round == 0) dispatch_round = 1;
        for (uint32_t i = 0; i < task_count; ++i) tasks[i].round_seen = 0;
        for (uint32_t offset = 0; offset < task_count; ++offset) {
            const uint32_t i = (start + offset) % task_count;
            const chimera_task_info &info = tasks[i].info;
            if (info.state != CHIMERA_TASK_READY || !cpu_allowed(info, cpu)) continue;
            if (best < 0 || info.priority > best_priority) {
                best = static_cast<int32_t>(i);
                best_priority = info.priority;
            }
        }
    }
    if (best >= 0) {
        tasks[static_cast<uint32_t>(best)].round_seen = dispatch_round;
        rr = (static_cast<uint32_t>(best) + 1u) % task_count;
    }
    return best;
}

static bool guards_ok(const Task &task) {
    for (uint32_t i = 0; i < 8u; ++i) {
        if (task.guard_low[i] != (0xA5A5A5A5A5A5A5A5ull ^ task.info.id)) return false;
        if (task.guard_high[i] != (0x5A5A5A5A5A5A5A5Aull ^ task.info.id)) return false;
    }
    return true;
}

static void install_frame(Task &task) {
    for (uint32_t i = 0; i < 8u; ++i) {
        task.guard_low[i] = 0xA5A5A5A5A5A5A5A5ull ^ task.info.id;
        task.guard_high[i] = 0x5A5A5A5A5A5A5A5Aull ^ task.info.id;
    }
    const uint64_t top = reinterpret_cast<uint64_t>(task.stack + TASK_STACK_BYTES);
    /* 15 saved GPRs + vector slot + RIP/CS/RFLAGS/RSP/SS = 21 qwords. */
    uint64_t *frame = reinterpret_cast<uint64_t *>(top - 168u);
    for (uint32_t i = 0; i < 21u; ++i) frame[i] = 0;
    frame[8] = reinterpret_cast<uint64_t>(&task);          /* RDI */
    frame[15] = 0;                                        /* stub vector slot */
    frame[16] = reinterpret_cast<uint64_t>(&koronos_context_trampoline);
    frame[17] = 0x08u;                                    /* kernel CS */
    frame[18] = 0x002u;                                   /* IF cleared until C entry */
    frame[19] = top;                                      /* kernel RSP after IRETQ */
    frame[20] = 0x10u;                                    /* kernel SS */
    task.ctx.rsp = reinterpret_cast<uint64_t>(frame);
    task.ctx.cr3 = kernel_cr3;
}

static void prepare_context(Task &task) {
    if (task.ctx.rsp == 0) install_frame(task);
    if (task.ctx.cr3 == 0) task.ctx.cr3 = kernel_cr3;
}

static void apply_pending_action(Task &task) {
    switch (task.pending_action) {
        case ACTION_BLOCK: task.info.state = CHIMERA_TASK_BLOCKED; break;
        case ACTION_EXIT: task.info.state = CHIMERA_TASK_EXITED; break;
        case ACTION_YIELD: task.info.state = CHIMERA_TASK_READY; break;
        default:
            if (task.info.state == CHIMERA_TASK_RUNNING) task.info.state = CHIMERA_TASK_READY;
            break;
    }
    task.pending_action = ACTION_NONE;
    task.info.ticks_remaining = DEFAULT_SLICE_TICKS;
}

/* Called with the scheduler lock held. */
static chimera_switch_target *select_next_locked(uint32_t cpu) {
    CpuState &s = cpu_state[cpu];
    const int32_t selected = pick_next_locked(cpu);
    if (selected < 0) {
        s.current_task = nullptr;
        s.target.ctx = &s.idle_ctx;
        s.target.cr3 = s.idle_ctx.cr3;
        return &s.target;
    }
    Task &task = tasks[static_cast<uint32_t>(selected)];
    task.info.state = CHIMERA_TASK_RUNNING;
    task.info.cpu = cpu;
    task.pending_action = ACTION_NONE;
    prepare_context(task);
    s.current_task = &task;
    s.current_cr3 = task.ctx.cr3;
    ++s.dispatched;
    s.target.ctx = &task.ctx;
    s.target.cr3 = task.ctx.cr3;
    return &s.target;
}

static int request_action(uint32_t cpu, uint8_t action) {
    if (cpu >= cpu_count) return -1;
    lock();
    Task *task = cpu_state[cpu].current_task;
    if (!task || task->info.state != CHIMERA_TASK_RUNNING) {
        /* Legacy cooperative callers are tracked in current_index[]. */
        const int32_t index = current_index[cpu];
        if (index < 0 || static_cast<uint32_t>(index) >= task_count ||
            tasks[static_cast<uint32_t>(index)].info.state != CHIMERA_TASK_RUNNING) {
            unlock();
            return -2;
        }
        task = &tasks[static_cast<uint32_t>(index)];
    }
    if (task->pending_action == ACTION_EXIT || task->pending_action == ACTION_BLOCK) {
        unlock();
        return -3;
    }
    if (action == ACTION_EXIT || action == ACTION_BLOCK || task->pending_action == ACTION_NONE)
        task->pending_action = action;
    unlock();
    return 0;
}

static void legacy_action(uint8_t action) {
    lock();
    int32_t owner = -1;
    uint32_t active = 0;
    for (uint32_t cpu = 0; cpu < cpu_count; ++cpu) {
        if (cpu_state[cpu].current_task) continue;
        if (current_index[cpu] >= 0) { owner = static_cast<int32_t>(cpu); ++active; }
    }
    unlock();
    if (active == 1) (void)request_action(static_cast<uint32_t>(owner), action);
}

static void parallel_worker(void *opaque) {
    ParallelWork *work = static_cast<ParallelWork *>(opaque);
    if (!work) return;
    const uint32_t cpu = koronos_preemptive_current_cpu();
    const uint32_t bit = 1u << (cpu < 32u ? cpu : 31u);
    work->cpu = cpu;
    work->apic_id = chimera_sched_apic_id(cpu);
    const uint64_t start = rdtsc64();
    if (cpu == 0) evidence.bsp_start_tsc = start;
    else evidence.ap_start_tsc = start;
    __sync_fetch_and_or(&evidence.active_mask, bit);

    uint64_t observed = 0;
    for (uint64_t i = 0; i < work->spins; ++i) {
        observed += ((i ^ static_cast<uint64_t>(cpu)) & 0xFull);
        if ((i & 0x3FFFu) == 0u) {
            __sync_fetch_and_or(&evidence.active_mask, bit);
            if ((evidence.active_mask & evidence.expected_mask) == evidence.expected_mask)
                __sync_fetch_and_add(&evidence.overlap_samples, 1u);
            pause_cpu();
        }
    }
    work->counted = observed + 1u;
    evidence.cpu_work[cpu] = work->counted;
    if (cpu == 0) evidence.bsp_end_tsc = rdtsc64();
    else evidence.ap_end_tsc = rdtsc64();
    __sync_fetch_and_or(&evidence.done_mask, bit);
    fence();
    chimera_sched_exit();
}

static uint32_t submit_parallel_worker(uint32_t cpu, uint64_t spins) {
    ParallelWork &work = parallel_work[cpu];
    work.fn = nullptr;
    work.cpu = cpu;
    work.apic_id = chimera_sched_apic_id(cpu);
    work.spins = spins;
    work.counted = 0;
    work.done = 0;
    work.info = chimera_task_info{};
    const int id = chimera_sched_submit(parallel_worker, &work, 200u);
    if (id < 0) return 0;
    (void)chimera_sched_set_affinity(static_cast<uint32_t>(id), 1ull << cpu);
    return 1u;
}

} // namespace

extern "C" void chimera_sched_init(uint32_t n) {
    lock();
    cpu_count = n ? n : 1;
    if (cpu_count > MAX_CPUS) cpu_count = MAX_CPUS;
    task_count = 0;
    rr = 0;
    dispatch_round = 1;
    next_id = 1;
    kernel_cr3 = 0;
    preemptive_ready = 0;
    total_switches = 0;
    total_preemptions = 0;
    total_ticks = 0;
    guard_failures_total = 0;
    for (uint32_t i = 0; i < MAX_TASKS; ++i) tasks[i] = Task{};
    for (uint32_t i = 0; i < MAX_CPUS; ++i) {
        cpu_state[i] = CpuState{};
        cpu_state[i].cpu = i;
        cpu_state[i].idle_ctx.cr3 = 0;
        current_index[i] = -1;
        parallel_work[i] = ParallelWork{};
    }
    evidence = ParallelEvidence{};
    unlock();
}

extern "C" uint32_t chimera_sched_cpu_count() {
    lock();
    const uint32_t n = cpu_count;
    unlock();
    return n;
}

extern "C" int chimera_sched_submit(chimera_task_fn fn, void *arg, uint32_t priority) {
    if (!fn) return -1;
    lock();
    if (task_count >= MAX_TASKS) { unlock(); return -2; }
    const uint32_t i = task_count++;
    tasks[i] = Task{};
    tasks[i].fn = fn;
    tasks[i].arg = arg;
    tasks[i].info = chimera_task_info{};
    tasks[i].info.id = next_id++;
    tasks[i].info.state = CHIMERA_TASK_READY;
    tasks[i].info.priority = priority;
    /* Production tasks are BSP-affine until explicitly dispatched to an AP. */
    tasks[i].info.affinity_mask = 1ull;
    tasks[i].info.ticks_remaining = DEFAULT_SLICE_TICKS;
    tasks[i].ctx.cr3 = kernel_cr3;
    const int id = static_cast<int>(tasks[i].info.id);
    unlock();
    return id;
}

extern "C" int chimera_sched_set_affinity(uint32_t task_id, uint64_t mask) {
    if (mask == 0) return -1;
    lock();
    for (uint32_t i = 0; i < task_count; ++i) {
        if (tasks[i].info.id == task_id && tasks[i].info.state != CHIMERA_TASK_EXITED) {
            tasks[i].info.affinity_mask = mask;
            unlock();
            return 0;
        }
    }
    unlock();
    return -2;
}

extern "C" int chimera_sched_set_task_cr3(uint32_t task_id, uint64_t cr3) {
    if ((cr3 & 0xFFFull) != 0) return -1;
    lock();
    for (uint32_t i = 0; i < task_count; ++i) {
        if (tasks[i].info.id == task_id) {
            tasks[i].ctx.cr3 = cr3;
            unlock();
            return 0;
        }
    }
    unlock();
    return -2;
}

extern "C" uint64_t chimera_sched_task_cr3(uint32_t task_id) {
    lock();
    uint64_t cr3 = 0;
    for (uint32_t i = 0; i < task_count; ++i)
        if (tasks[i].info.id == task_id) { cr3 = tasks[i].ctx.cr3; break; }
    unlock();
    return cr3;
}

extern "C" int chimera_sched_preemptive_init(uint32_t n) {
    lock();
    if (n && n < MAX_CPUS) cpu_count = n;
    __asm__ volatile("mov %%cr3, %0" : "=r"(kernel_cr3) : : "memory");
    for (uint32_t i = 0; i < MAX_CPUS; ++i) cpu_state[i].idle_ctx.cr3 = kernel_cr3;
    preemptive_ready = 1;
    unlock();
    return 0;
}

extern "C" int chimera_sched_preemptive_ready() { return preemptive_ready ? 1 : 0; }

extern "C" void *chimera_sched_cpu_state(uint32_t cpu) {
    return cpu < MAX_CPUS ? &cpu_state[cpu] : nullptr;
}

extern "C" void chimera_sched_set_cpu_online(uint32_t cpu, uint32_t apic_id) {
    if (cpu >= MAX_CPUS) return;
    cpu_state[cpu].online = 1;
    cpu_state[cpu].apic_id = apic_id;
}

extern "C" uint32_t chimera_sched_cpu_online(uint32_t cpu) {
    return cpu < MAX_CPUS ? cpu_state[cpu].online : 0;
}

extern "C" uint32_t chimera_sched_apic_id(uint32_t cpu) {
    return cpu < MAX_CPUS ? cpu_state[cpu].apic_id : 0;
}

extern "C" void *chimera_sched_irq_handler(uint64_t vector) {
    uint32_t cpu = koronos_preemptive_current_cpu();
    if (cpu >= cpu_count) cpu = 0;
    CpuState &s = cpu_state[cpu];
    const bool tick = vector == KORONOS_TIMER_VECTOR_PIT ||
                      vector == KORONOS_TIMER_VECTOR_AP_TICK;
    if (tick) {
        ++s.ticks;
        ++total_ticks;
    }

    Task *current = s.current_task;
    bool must_switch = current == nullptr;
    if (current) {
        if (tick) {
            ++current->info.total_ticks;
            if (current->info.ticks_remaining > 0) --current->info.ticks_remaining;
        }
        if (!guards_ok(*current)) {
            ++s.guard_failures;
            ++guard_failures_total;
        }
        ++s.switches;
        ++total_switches;
        if (vector == KORONOS_TIMER_VECTOR_YIELD ||
            vector == KORONOS_TIMER_VECTOR_AP_WORK) {
            must_switch = true;
        } else if (tick && current->info.ticks_remaining == 0) {
            ++s.preemptions;
            ++current->info.preemptions;
            ++total_preemptions;
            must_switch = true;
        }
    }
    if (!must_switch) return nullptr;

    lock();
    if (current) apply_pending_action(*current);
    chimera_switch_target *target = select_next_locked(cpu);
    unlock();
    return target;
}

extern "C" uint32_t chimera_sched_run_preemptive(uint32_t cpu) {
    if (!preemptive_ready || cpu >= cpu_count || cpu >= MAX_CPUS) return 0;
    CpuState &s = cpu_state[cpu];
    if (s.in_loop) return 0;
    s.in_loop = 1;
    s.current_task = nullptr;
    s.current_ctx = &s.idle_ctx;
    const uint32_t before = s.dispatched;
    koronos_preempt_yield();
    s.in_loop = 0;
    return s.dispatched - before;
}

extern "C" void chimera_sched_task_entry(void *opaque) {
    Task *task = static_cast<Task *>(opaque);
    const uint64_t begin = reinterpret_cast<uint64_t>(&tasks[0]);
    const uint64_t end = reinterpret_cast<uint64_t>(&tasks[MAX_TASKS]);
    const uint64_t addr = reinterpret_cast<uint64_t>(task);
    if (addr < begin || addr >= end) {
        for (;;) __asm__ volatile("hlt");
    }
    const uint32_t cpu = koronos_preemptive_current_cpu();
    cpu_state[cpu].current_task = task;
    cpu_state[cpu].current_ctx = &task->ctx;
    __asm__ volatile("sti" ::: "memory");
    ++task->entry_count;
    task->fn(task->arg);
    chimera_sched_exit();
    for (;;) chimera_sched_yield();
}

extern "C" uint32_t chimera_sched_run_once(uint32_t cpu) {
    lock();
    if (cpu >= cpu_count) { unlock(); return 0; }
    if (cpu_state[cpu].current_task) { unlock(); return 0; }
    if (current_index[cpu] >= 0) { unlock(); return 0; }
    chimera_task_fn fn = nullptr;
    void *arg = nullptr;
    uint32_t index = 0;
    const int32_t selected = pick_next_locked(cpu);
    if (selected < 0) { unlock(); return 0; }
    index = static_cast<uint32_t>(selected);
    tasks[index].info.state = CHIMERA_TASK_RUNNING;
    tasks[index].info.cpu = cpu;
    tasks[index].pending_action = ACTION_NONE;
    current_index[cpu] = static_cast<int32_t>(index);
    fn = tasks[index].fn;
    arg = tasks[index].arg;
    unlock();

    fn(arg);

    lock();
    Task &t = tasks[index];
    ++t.info.runs;
    ++t.info.ticks;
    t.info.total_ticks += DEFAULT_SLICE_TICKS;
    apply_pending_action(t);
    if (current_index[cpu] == static_cast<int32_t>(index)) current_index[cpu] = -1;
    unlock();
    ++cpu_state[cpu].work_count;
    return 1;
}

extern "C" uint32_t chimera_sched_run_serial_range(uint32_t first_cpu, uint32_t n) {
    lock();
    const uint32_t total = cpu_count;
    unlock();
    if (first_cpu >= total || n == 0) return 0;
    uint32_t end = first_cpu + n;
    if (end < first_cpu || end > total) end = total;
    uint32_t ran = 0;
    for (uint32_t cpu = first_cpu; cpu < end; ++cpu) ran += chimera_sched_run_once(cpu);
    return ran;
}

extern "C" uint32_t chimera_sched_run_parallel(uint32_t first_cpu, uint32_t n) {
    if (!preemptive_ready || n == 0 || first_cpu == 0 || first_cpu >= cpu_count) return 0;
    parallel_lock_acquire();

    lock();
    uint32_t end = first_cpu + n;
    if (end < first_cpu || end > cpu_count) end = cpu_count;
    evidence.active_mask = 0;
    evidence.done_mask = 0;
    evidence.overlap_samples = 0;
    evidence.expected_mask = 1u;
    for (uint32_t c = 0; c < MAX_CPUS; ++c) {
        evidence.cpu_work[c] = 0;
        evidence.cpu_tasks[c] = 0;
    }
    evidence.bsp_start_tsc = 0;
    evidence.ap_start_tsc = 0;
    evidence.bsp_end_tsc = 0;
    evidence.ap_end_tsc = 0;
    unlock();

    /* Submission helpers acquire the scheduler lock themselves; do not hold it
     * here or the non-recursive spinlock deadlocks on the BSP. */
    uint32_t submitted = 0;
    submitted += submit_parallel_worker(0, 2200000ull);
    for (uint32_t cpu = first_cpu; cpu < end; ++cpu) {
        if (!cpu_state[cpu].online) continue;
        lock();
        evidence.expected_mask |= (1u << (cpu < 32u ? cpu : 31u));
        unlock();
        submitted += submit_parallel_worker(cpu, 2400000ull + cpu * 65536ull);
    }

    for (uint32_t cpu = first_cpu; cpu < end; ++cpu) {
        if (cpu_state[cpu].online) (void)koronos_preemptive_send_ipi(cpu, KORONOS_TIMER_VECTOR_AP_WORK);
    }
    (void)chimera_sched_run_preemptive(0);

    uint64_t spins = 0;
    while ((evidence.done_mask & evidence.expected_mask) != evidence.expected_mask &&
           spins++ < 2000000000ull) pause_cpu();
    fence();

    uint32_t executed_on_aps = 0;
    lock();
    for (uint32_t cpu = first_cpu; cpu < end; ++cpu) {
        if (!cpu_state[cpu].online) continue;
        const uint32_t bit = 1u << (cpu < 32u ? cpu : 31u);
        if ((evidence.done_mask & bit) != 0 && parallel_work[cpu].counted != 0) {
            evidence.cpu_tasks[cpu] = 1;
            ++executed_on_aps;
            ++cpu_state[cpu].work_count;
        }
    }
    evidence.cpu_tasks[0] = (evidence.done_mask & 1u) != 0 ? 1u : 0u;
    unlock();
    parallel_lock_release();
    return executed_on_aps;
}

extern "C" int chimera_sched_yield_on_cpu(uint32_t cpu) { return request_action(cpu, ACTION_YIELD); }
extern "C" int chimera_sched_block_on_cpu(uint32_t cpu) { return request_action(cpu, ACTION_BLOCK); }
extern "C" int chimera_sched_exit_on_cpu(uint32_t cpu) { return request_action(cpu, ACTION_EXIT); }

extern "C" void chimera_sched_yield(void) {
    const uint32_t cpu = koronos_preemptive_current_cpu();
    if (cpu < cpu_count && cpu_state[cpu].current_task) {
        (void)request_action(cpu, ACTION_YIELD);
        koronos_preempt_yield();
    } else {
        legacy_action(ACTION_YIELD);
    }
}
extern "C" void chimera_sched_block(void) {
    const uint32_t cpu = koronos_preemptive_current_cpu();
    if (cpu < cpu_count && cpu_state[cpu].current_task) {
        (void)request_action(cpu, ACTION_BLOCK);
        koronos_preempt_yield();
    } else {
        legacy_action(ACTION_BLOCK);
    }
}
extern "C" void chimera_sched_wake(uint32_t id) {
    lock();
    for (uint32_t i = 0; i < task_count; ++i)
        if (tasks[i].info.id == id && tasks[i].info.state == CHIMERA_TASK_BLOCKED)
            tasks[i].info.state = CHIMERA_TASK_READY;
    unlock();
}
extern "C" void chimera_sched_exit(void) {
    const uint32_t cpu = koronos_preemptive_current_cpu();
    if (cpu < cpu_count && cpu_state[cpu].current_task) {
        (void)request_action(cpu, ACTION_EXIT);
        koronos_preempt_yield();
    } else {
        legacy_action(ACTION_EXIT);
    }
}

extern "C" uint32_t chimera_sched_runnable_count() {
    lock();
    uint32_t n = 0;
    for (uint32_t i = 0; i < task_count; ++i)
        if (tasks[i].info.state == CHIMERA_TASK_READY) ++n;
    unlock();
    return n;
}

extern "C" uint32_t chimera_sched_snapshot(chimera_task_info *out, uint32_t cap) {
    if (!out) return 0;
    lock();
    const uint32_t n = task_count < cap ? task_count : cap;
    for (uint32_t i = 0; i < n; ++i) out[i] = tasks[i].info;
    unlock();
    return n;
}

extern "C" uint32_t chimera_sched_preemptive_dispatches(uint32_t cpu) {
    return cpu < MAX_CPUS ? cpu_state[cpu].dispatched : 0;
}
extern "C" uint32_t chimera_sched_preemptive_switches(uint32_t cpu) {
    return cpu < MAX_CPUS ? cpu_state[cpu].switches : 0;
}
extern "C" uint32_t chimera_sched_preemptive_ticks(uint32_t cpu) {
    return cpu < MAX_CPUS ? cpu_state[cpu].ticks : 0;
}
extern "C" uint32_t chimera_sched_preemptive_preemptions(uint32_t cpu) {
    return cpu < MAX_CPUS ? cpu_state[cpu].preemptions : 0;
}
extern "C" uint32_t chimera_sched_guard_failures() { return guard_failures_total; }
extern "C" uint64_t chimera_sched_total_context_switches() { return total_switches; }
extern "C" uint64_t chimera_sched_total_preemptions() { return total_preemptions; }
extern "C" uint64_t chimera_sched_total_timer_ticks() { return total_ticks; }
extern "C" uint32_t chimera_sched_parallel_overlap() { return evidence.overlap_samples; }
extern "C" uint32_t chimera_sched_parallel_cpu_tasks(uint32_t cpu) {
    return cpu < MAX_CPUS ? evidence.cpu_tasks[cpu] : 0;
}
extern "C" uint64_t chimera_sched_parallel_cpu_work(uint32_t cpu) {
    return cpu < MAX_CPUS ? evidence.cpu_work[cpu] : 0;
}
extern "C" void chimera_sched_parallel_timestamps(uint64_t *bsp_start, uint64_t *ap_start,
                                                  uint64_t *bsp_end, uint64_t *ap_end) {
    if (bsp_start) *bsp_start = evidence.bsp_start_tsc;
    if (ap_start) *ap_start = evidence.ap_start_tsc;
    if (bsp_end) *bsp_end = evidence.bsp_end_tsc;
    if (ap_end) *ap_end = evidence.ap_end_tsc;
}
