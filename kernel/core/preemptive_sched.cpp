#include "chimera/preemptive_sched.h"
#include "chimera/scheduler.h"
#include "chimera/interrupt.h"

/* Read directly by arch/x86_64/interrupts.asm and context_switch.asm. */
extern "C" {
void *koronos_preempt_current_ctx = nullptr;
void *koronos_preempt_current_task = nullptr;
void koronos_context_trampoline(void);
}

namespace {

constexpr uint32_t MAX_TASKS = 4u;
constexpr uint32_t TASK_STACK_BYTES = 16u * 1024u;
constexpr uint32_t TIMER_QUANTUM_TICKS = 1u;
constexpr uint32_t WATCHDOG_SWITCHES = 1024u;
constexpr uint32_t TASK_ITERATIONS = 8u;
constexpr uint32_t TASK_SPIN = 2000000u;
constexpr uint64_t VECTOR_PIT = 32u;
constexpr uint64_t VECTOR_YIELD = 33u;
constexpr uint32_t TASK_READY = 0u;
constexpr uint32_t TASK_RUNNING = 1u;
constexpr uint32_t TASK_EXITED = 2u;

struct Context {
    uint64_t rsp;        /* offset 0 is consumed by the assembly switch */
    uint64_t stack_top;
    uint64_t stack_bottom;
};

struct Task {
    Context ctx;
    chimera_task_fn fn;
    void *arg;
    uint32_t id;
    volatile uint32_t state;
    uint64_t runs;
    uint64_t ticks;
    uint64_t preempted;
    uint64_t guard_low[8];
    alignas(16) uint8_t stack[TASK_STACK_BYTES];
    uint64_t guard_high[8];
};

Task tasks[MAX_TASKS];
Context idle_ctx;
volatile uint32_t running = 0;
volatile uint32_t selftest_done = 0;
volatile uint32_t timer_ticks = 0;
volatile uint32_t timer_preempt_count = 0;
volatile uint32_t switch_count = 0;
volatile uint32_t guard_failures = 0;
volatile uint32_t task_a_runs = 0;
volatile uint32_t task_b_runs = 0;
volatile uint32_t interleavings = 0;
volatile uint8_t order[64];
volatile uint32_t order_len = 0;

static inline void out8(uint16_t port, uint8_t value) {
    __asm__ volatile("outb %0, %1" : : "a"(value), "Nd"(port));
}

static inline void io_wait() { out8(0x80, 0); }

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

static void debug_order() {
    char line[80];
    const char *label = "[PMT ] order=";
    unsigned int pos = 0;
    while (label[pos] && pos + 1u < sizeof(line)) { line[pos] = label[pos]; ++pos; }
    for (uint32_t i = 0; i < order_len && pos + 1u < sizeof(line); ++i) {
        line[pos++] = static_cast<char>(order[i]);
    }
    line[pos] = 0;
    debug_write(line);
}

static void record(uint8_t marker) {
    /* Tasks run with IF=1; keep the index increment and marker store atomic so
     * a timer preemption cannot split interleaving evidence. */
    __asm__ volatile("cli" ::: "memory");
    if (order_len < sizeof(order)) {
        const uint32_t index = order_len++;
        if (index && order[index - 1u] != marker) ++interleavings;
        order[index] = marker;
    }
    __asm__ volatile("sti" ::: "memory");
}

static void guarded_spin() {
    for (volatile uint32_t i = 0; i < TASK_SPIN; ++i) __asm__ volatile("pause" ::: "memory");
}

static void task_a(void *) {
    for (uint32_t i = 0; i < TASK_ITERATIONS; ++i) {
        record('A');
        ++task_a_runs;
        guarded_spin();
    }
}

static void task_b(void *) {
    for (uint32_t i = 0; i < TASK_ITERATIONS; ++i) {
        record('B');
        ++task_b_runs;
        guarded_spin();
    }
}

static bool guards_ok(const Task &task, uint32_t id) {
    for (uint32_t i = 0; i < 8u; ++i) {
        if (task.guard_low[i] != (0xA5A5A5A5A5A5A5A5ull ^ id)) return false;
        if (task.guard_high[i] != (0x5A5A5A5A5A5A5A5Aull ^ id)) return false;
    }
    return true;
}

static void install_frame(Task &task, chimera_task_fn fn, void *arg, uint32_t id) {
    task.fn = fn;
    task.arg = arg;
    task.id = id;
    task.state = TASK_READY;
    task.runs = 0;
    task.ticks = 0;
    task.preempted = 0;
    for (uint32_t i = 0; i < 8u; ++i) {
        task.guard_low[i] = 0xA5A5A5A5A5A5A5A5ull ^ id;
        task.guard_high[i] = 0x5A5A5A5A5A5A5A5Aull ^ id;
    }

    const uint64_t top = reinterpret_cast<uint64_t>(task.stack + TASK_STACK_BYTES);
    /* Layout consumed by koronos_preempt_common after the 15 GPR pushes:
     *   [0..14]  r15, r14, r13, r12, r11, r10, r9, r8, rdi, rsi, rbp, rbx,
     *            rdx, rcx, rax
     *   [15]     stub vector slot (discarded before IRETQ)
     *   [16..18] RIP/CS/RFLAGS consumed by IRETQ
     *   [19..20] RSP/SS consumed by IRETQ (mandatory in long mode)
     * RDI carries this task's pointer so the first-run trampoline never needs
     * the mutable global current-task value. IF is cleared until the C entry
     * enables it, preventing a timer IRQ from splitting the trampoline.
     * After IRETQ the task starts with RSP == top. */
    uint64_t *frame = reinterpret_cast<uint64_t *>(top - 168u);
    for (uint32_t i = 0; i < 15u; ++i) frame[i] = 0;
    frame[8] = reinterpret_cast<uint64_t>(&task);
    frame[15] = 0;
    frame[16] = reinterpret_cast<uint64_t>(&koronos_context_trampoline);
    frame[17] = 0x08u;                               /* kernel CS */
    frame[18] = 0x002u;                              /* kernel RFLAGS, IF=0 */
    frame[19] = top;                                 /* kernel RSP after IRETQ */
    frame[20] = 0x10u;                               /* kernel SS */
    task.ctx.rsp = reinterpret_cast<uint64_t>(frame);
    task.ctx.stack_top = top;
    task.ctx.stack_bottom = reinterpret_cast<uint64_t>(task.stack);
}

static uint32_t next_task_index(uint32_t current_id) {
    for (uint32_t offset = 1u; offset <= MAX_TASKS; ++offset) {
        const uint32_t index = (current_id - 1u + offset) % MAX_TASKS;
        if (tasks[index].state == TASK_READY) return index;
    }
    const uint32_t current_index = current_id ? current_id - 1u : 0u;
    if (tasks[current_index].state == TASK_READY) return current_index;
    return MAX_TASKS; /* idle context */
}

static uint64_t select_next_context() {
    Task *current = static_cast<Task *>(koronos_preempt_current_task);
    const uint32_t current_id = current ? current->id : 0u;
    const uint32_t index = next_task_index(current_id);
    /* Do not update current_ctx here: interrupts.asm stores the outgoing RSP
     * through that pointer before installing the returned context. */
    if (index == MAX_TASKS) {
        koronos_preempt_current_task = nullptr;
        return reinterpret_cast<uint64_t>(&idle_ctx);
    }
    Task *next = &tasks[index];
    next->state = TASK_RUNNING;
    koronos_preempt_current_task = next;
    return reinterpret_cast<uint64_t>(&next->ctx);
}

static void timer_setup() {
    out8(0x20, 0x11); io_wait();
    out8(0xA0, 0x11); io_wait();
    out8(0x21, 0x20); io_wait();
    out8(0xA1, 0x28); io_wait();
    out8(0x21, 0x04); io_wait();
    out8(0xA1, 0x02); io_wait();
    out8(0x21, 0x01); io_wait();
    out8(0xA1, 0x01); io_wait();

    const uint16_t divisor = 11932; /* ~100 Hz */
    out8(0x43, 0x36);
    out8(0x40, static_cast<uint8_t>(divisor & 0xFFu));
    out8(0x40, static_cast<uint8_t>(divisor >> 8));
    out8(0x21, 0xFE); /* IRQ0 only */
    out8(0xA1, 0xFF);
}

static void timer_stop() {
    out8(0x21, 0xFF);
    out8(0xA1, 0xFF);
}

} // namespace

extern "C" void koronos_preempt_yield(void) {
    /* Dedicated supervisor software gate; no PIC EOI, unlike PIT vector 32. */
    __asm__ volatile("int $0x21" ::: "memory");
}

extern "C" uint64_t koronos_preempt_irq_handler(uint64_t vector) {
    if (!running) return 0;

    if (vector == VECTOR_PIT) {
        out8(0x20, 0x20);
        ++timer_ticks;
        Task *current = static_cast<Task *>(koronos_preempt_current_task);
        if (current) ++current->ticks;
        if (timer_ticks % TIMER_QUANTUM_TICKS != 0u) return 0;
    } else if (vector != VECTOR_YIELD) {
        return 0;
    }

    Task *current = static_cast<Task *>(koronos_preempt_current_task);
    if (current) {
        if (current->state == TASK_RUNNING) current->state = TASK_READY;
        if (vector == VECTOR_PIT) ++current->preempted;
        if (!guards_ok(*current, current->id)) ++guard_failures;
    }

    if (vector == VECTOR_PIT) ++timer_preempt_count;
    ++switch_count;

    if (switch_count >= WATCHDOG_SWITCHES) {
        running = 0;
        timer_stop();
        koronos_preempt_current_task = nullptr;
        return reinterpret_cast<uint64_t>(&idle_ctx);
    }
    return select_next_context();
}

extern "C" void koronos_preempt_task_entry(void *opaque) {
    const uint64_t addr = reinterpret_cast<uint64_t>(opaque);
    const uint64_t begin = reinterpret_cast<uint64_t>(&tasks[0]);
    const uint64_t end = reinterpret_cast<uint64_t>(&tasks[MAX_TASKS]);
    if (addr < begin || addr >= end) {
        debug_write("[PMT ] FAIL: trampoline argument outside task array");
        for (;;) __asm__ volatile("hlt");
    }

    Task *task = static_cast<Task *>(opaque);
    koronos_preempt_current_task = task;
    koronos_preempt_current_ctx = &task->ctx;
    debug_u32("[PMT ] task entry id=", task->id);
    /* The crafted frame enters with IF=0 so the trampoline cannot be preempted
     * before it has consumed RDI. Enable timer preemption only now. */
    __asm__ volatile("sti" ::: "memory");
    ++task->runs;
    task->fn(task->arg);
    task->state = TASK_EXITED;
    for (;;) koronos_preempt_yield();
}

extern "C" int koronos_preemptive_selftest(void) {
    if (selftest_done) return 0;
    selftest_done = 1;

    for (uint32_t i = 0; i < MAX_TASKS; ++i) tasks[i] = Task{};
    idle_ctx = Context{};
    koronos_preempt_current_ctx = &idle_ctx;
    koronos_preempt_current_task = nullptr;
    timer_ticks = 0;
    timer_preempt_count = 0;
    switch_count = 0;
    guard_failures = 0;
    task_a_runs = 0;
    task_b_runs = 0;
    interleavings = 0;
    order_len = 0;

    install_frame(tasks[0], task_a, nullptr, 1u);
    install_frame(tasks[1], task_b, nullptr, 2u);
    /* Zero-initialized Task objects otherwise look READY with a null context. */
    tasks[2].state = TASK_EXITED;
    tasks[3].state = TASK_EXITED;

    debug_write("[PMT ] entering timer-preempted task runtime");
    __asm__ volatile("cli" ::: "memory");
    if (chimera_interrupt_init() != 0) {
        debug_write("[PMT ] FAIL: IDT initialization failed");
        return -1;
    }
    timer_setup();
    running = 1;
    /* Deliberate software entry: the CPU saves an idle interrupt frame on the
     * caller's stack, which the assembly switch stores in idle_ctx. */
    koronos_preempt_yield();
    __asm__ volatile("cli" ::: "memory");
    running = 0;
    timer_stop();
    debug_write("[PMT ] returned from preempt runtime");

    bool saw_a = false, saw_b = false;
    for (uint32_t i = 0; i < order_len; ++i) {
        saw_a = saw_a || order[i] == 'A';
        saw_b = saw_b || order[i] == 'B';
    }
    bool guards = true;
    for (uint32_t i = 0; i < 2u; ++i) guards = guards && guards_ok(tasks[i], i + 1u);
    const bool pass = saw_a && saw_b && interleavings >= 6u &&
                      task_a_runs == TASK_ITERATIONS && task_b_runs == TASK_ITERATIONS &&
                      timer_preempt_count >= 4u && switch_count >= 6u &&
                      tasks[0].state == TASK_EXITED && tasks[1].state == TASK_EXITED &&
                      switch_count < WATCHDOG_SWITCHES &&
                      guard_failures == 0u && guards;

    debug_write("[PMT ] x86_64 CALLEE-SAVED CONTEXT SWITCH (GPR+RSP+IRETQ)");
    debug_write(pass ? "[PMT ] SELFTEST PASS" : "[PMT ] SELFTEST FAIL");
    debug_u32("[PMT ] task_A_iterations=", task_a_runs);
    debug_u32("[PMT ] task_B_iterations=", task_b_runs);
    debug_u32("[PMT ] timer_preemptions=", timer_preempt_count);
    debug_u32("[PMT ] context_switches=", switch_count);
    debug_u32("[PMT ] interleavings=", interleavings);
    debug_u32("[PMT ] guard_failures=", guard_failures);
    debug_order();
    return pass ? 0 : -1;
}

extern "C" uint32_t koronos_preemptive_switch_count(void) { return switch_count; }
extern "C" uint32_t koronos_preemptive_timer_count(void) { return timer_preempt_count; }
extern "C" uint32_t koronos_preemptive_guard_failures(void) { return guard_failures; }
extern "C" uint32_t koronos_preemptive_interleavings(void) { return interleavings; }
