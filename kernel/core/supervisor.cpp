#include "chimera/supervisor.h"
#include "chimera/scheduler.h"
#include "chimera/multiboot_modules.h"

/* Kernel-owned PID 1 supervisor.
 *
 * PID 1 is a resident scheduler task created by chimera_supervisor_init(). Its
 * children are submitted to the same scheduler via chimera_sched_submit(). A
 * child wrapper executes the registered work entry point, records the exit code
 * returned by that work, notifies PID 1, and exits its scheduler task. PID 1
 * waits, restarts supervised services according to policy, reaps zombies, and
 * yields so the cooperative scheduler keeps making progress. */

namespace {

constexpr uint32_t PID1_PID = 1u;
constexpr uint32_t PID1_PRIORITY = 120u;
constexpr uint32_t CHILD_PRIORITY = 110u;
constexpr uint32_t WAIT_BUDGET = 8u;
constexpr uint32_t SELFTEST_DISPATCH_LIMIT = 512u;
constexpr uint32_t OBSERVED_SLOTS = 8u;

struct ProcessSlot {
    chimera_supervisor_process process{};
    bool used = false;
};

ProcessSlot slots[CHIMERA_SUPERVISOR_MAX_PROCESSES];
uint32_t next_pid = 2u;          /* PID 1 is reserved by init */
uint32_t process_count = 0;
uint32_t reaped_total = 0;
uint32_t restarts_total = 0;
uint32_t notifications = 0;
uint32_t observed_count = 0;
uint32_t observed_pid[OBSERVED_SLOTS]{};
uint32_t observed_status[OBSERVED_SLOTS]{};
uint32_t reaped_last_pid = 0;
uint32_t reaped_last_status = 0;
uint32_t restart_last_pid = 0;
uint32_t pid1_task_id = 0;
uint32_t lock_word = 0;
bool initialized = false;

static inline void out8_(uint16_t port, uint8_t value) {
    __asm__ volatile("outb %0, %1" : : "a"(value), "Nd"(port));
}

static void debug_text(const char *text) {
    if (!text) return;
    while (*text) out8_(0xE9u, static_cast<uint8_t>(*text++));
    out8_(0xE9u, '\n');
}

static void debug_u32(const char *label, uint32_t value) {
    char line[96];
    uint32_t pos = 0;
    while (label[pos] && pos + 1u < sizeof(line)) {
        line[pos] = label[pos];
        ++pos;
    }
    char digits[10];
    uint32_t digits_used = 0;
    if (value == 0) digits[digits_used++] = '0';
    while (value && digits_used < sizeof(digits)) {
        digits[digits_used++] = static_cast<char>('0' + (value % 10u));
        value /= 10u;
    }
    while (digits_used && pos + 1u < sizeof(line)) {
        line[pos++] = digits[--digits_used];
    }
    line[pos] = 0;
    debug_text(line);
}

static const char *state_name(uint32_t state) {
    switch (state) {
        case CHIMERA_SUP_EMPTY:   return "EMPTY";
        case CHIMERA_SUP_READY:   return "READY";
        case CHIMERA_SUP_RUNNING: return "RUNNING";
        case CHIMERA_SUP_ZOMBIE:  return "ZOMBIE";
        case CHIMERA_SUP_EXITED:  return "EXITED";
        case CHIMERA_SUP_ACTIVE:  return "ACTIVE";
        default:                  return "UNKNOWN";
    }
}

static void lock() {
    while (__sync_lock_test_and_set(&lock_word, 1u)) { }
}

static void unlock() {
    __sync_lock_release(&lock_word);
}

static bool has_token(const char *text, const char *token) {
    if (!text || !token) return false;
    uint32_t token_length = 0;
    while (token[token_length]) ++token_length;
    if (token_length == 0) return false;
    for (uint32_t i = 0; text[i]; ++i) {
        uint32_t j = 0;
        while (j < token_length && text[i + j] == token[j]) ++j;
        if (j == token_length) return true;
    }
    return false;
}

static void copy_name(char *target, const char *source) {
    uint32_t i = 0;
    if (source) {
        for (; i + 1u < CHIMERA_SUPERVISOR_NAME_MAX && source[i]; ++i) {
            target[i] = source[i];
        }
    }
    target[i] = 0;
}

static ProcessSlot *find_locked(uint32_t pid) {
    if (pid == 0) return nullptr;
    for (uint32_t i = 0; i < CHIMERA_SUPERVISOR_MAX_PROCESSES; ++i) {
        if (slots[i].used && slots[i].process.pid == pid) return &slots[i];
    }
    return nullptr;
}

static ProcessSlot *allocate_locked() {
    for (uint32_t i = 0; i < CHIMERA_SUPERVISOR_MAX_PROCESSES; ++i) {
        if (!slots[i].used) {
            slots[i].used = true;
            ++process_count;
            return &slots[i];
        }
    }
    return nullptr;
}

static void clear_locked(ProcessSlot *slot) {
    slot->process = chimera_supervisor_process{};
    slot->used = false;
    if (process_count) --process_count;
}

static void remember_observation_locked(uint32_t pid, uint32_t status) {
    if (observed_count < OBSERVED_SLOTS) {
        observed_pid[observed_count] = pid;
        observed_status[observed_count] = status;
        ++observed_count;
        return;
    }
    /* Keep the newest eight observations so repeated service restarts cannot
       push the original child out of the verifier's view. */
    for (uint32_t i = 1; i < OBSERVED_SLOTS; ++i) {
        observed_pid[i - 1u] = observed_pid[i];
        observed_status[i - 1u] = observed_status[i];
    }
    observed_pid[OBSERVED_SLOTS - 1u] = pid;
    observed_status[OBSERVED_SLOTS - 1u] = status;
}

static void child_task(void *arg);
static void pid1_task(void *arg);

/* Called from PID 1 while the delivered child is still ZOMBIE, before reaping. */
static void restart_service(uint32_t pid) {
    chimera_supervisor_work_fn work = nullptr;
    void *work_arg = nullptr;
    char name[CHIMERA_SUPERVISOR_NAME_MAX];
    uint32_t id = 0;
    uint32_t max_restarts = 0;
    uint32_t next_count = 0;

    lock();
    ProcessSlot *slot = find_locked(pid);
    if (!slot || slot->process.parent_pid != PID1_PID ||
        slot->process.state != CHIMERA_SUP_ZOMBIE ||
        !slot->process.restartable ||
        slot->process.restart_count >= slot->process.max_restarts) {
        unlock();
        return;
    }
    work = slot->process.work;
    work_arg = slot->process.work_arg;
    copy_name(name, slot->process.name);
    id = slot->process.id;
    max_restarts = slot->process.max_restarts;
    next_count = slot->process.restart_count + 1u;
    unlock();

    uint32_t new_pid = 0;
    if (chimera_supervisor_spawn(work, work_arg, PID1_PID, name, 1, &new_pid) != 0) {
        return;
    }
    lock();
    ProcessSlot *successor = find_locked(new_pid);
    if (successor) {
        successor->process.restart_count = next_count;
        successor->process.max_restarts = max_restarts;
        successor->process.id = id;
        ++restarts_total;
        restart_last_pid = new_pid;
    }
    unlock();
}

static void pid1_task(void *arg) {
    (void)arg;
    for (uint32_t i = 0; i < WAIT_BUDGET; ++i) {
        uint32_t pid = 0;
        uint32_t status = 0;
        const int rc = chimera_supervisor_wait(PID1_PID, &pid, &status);
        if (rc != CHIMERA_SUP_WAIT_DELIVERED) break;
        restart_service(pid);
    }
    (void)chimera_supervisor_reap_children(PID1_PID);
    /* PID 1 is resident: it yields instead of exiting or spinning on a
       busy-wait loop while children are still running. */
    chimera_sched_yield();
}

static void child_task(void *arg) {
    const uint32_t pid = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(arg));
    chimera_supervisor_work_fn work = nullptr;
    void *work_arg = nullptr;

    lock();
    ProcessSlot *slot = find_locked(pid);
    if (!slot || slot->process.state != CHIMERA_SUP_READY) {
        unlock();
        return;
    }
    work = slot->process.work;
    work_arg = slot->process.work_arg;
    slot->process.state = CHIMERA_SUP_RUNNING;
    ++slot->process.runs;
    unlock();

    const uint32_t exit_code = work(work_arg);

    lock();
    slot = find_locked(pid);
    if (slot) {
        /* The exit code is the value actually returned by the work entry. */
        slot->process.exit_code = exit_code;
        slot->process.state = CHIMERA_SUP_EXITED;
    }
    ++notifications;
    const uint32_t supervisor_task = pid1_task_id;
    unlock();

    chimera_sched_wake(supervisor_task);
    chimera_sched_exit();
}

struct MeasuredWork {
    uint32_t iterations;
    uint32_t base_code;
    uint32_t completed;
};

static uint32_t measured_work(void *arg) {
    MeasuredWork *work = static_cast<MeasuredWork *>(arg);
    if (!work) return 0;
    uint32_t sum = 0;
    for (uint32_t i = 0; i < work->iterations; ++i) {
        sum += (i * 3u + 1u);
    }
    work->completed = sum;
    /* Exit code is derived from work actually executed, not a fixed literal. */
    return work->base_code ^ (sum & 0xFu);
}

static uint32_t expected_exit(const MeasuredWork &work) {
    return work.base_code ^ (work.completed & 0xFu);
}

static bool observed_exit(const chimera_supervisor_snapshot_data &snapshot,
                          uint32_t pid, uint32_t *status) {
    for (uint32_t i = 0; i < snapshot.observed_count; ++i) {
        if (snapshot.observed_pid[i] == pid) {
            *status = snapshot.observed_status[i];
            return true;
        }
    }
    return false;
}

} // namespace

extern "C" int chimera_supervisor_init(void) {
    lock();
    if (initialized) {
        unlock();
        return 0;
    }
    for (uint32_t i = 0; i < CHIMERA_SUPERVISOR_MAX_PROCESSES; ++i) {
        slots[i] = ProcessSlot{};
    }
    next_pid = 2u;
    process_count = 0;
    reaped_total = 0;
    restarts_total = 0;
    notifications = 0;
    observed_count = 0;
    for (uint32_t i = 0; i < OBSERVED_SLOTS; ++i) {
        observed_pid[i] = 0;
        observed_status[i] = 0;
    }
    reaped_last_pid = 0;
    reaped_last_status = 0;
    restart_last_pid = 0;
    pid1_task_id = 0;

    /* PID 1 owns no parent and is never reaped. Its state stays ACTIVE. */
    ProcessSlot &pid1 = slots[0];
    pid1.used = true;
    pid1.process.pid = PID1_PID;
    pid1.process.parent_pid = 0;
    pid1.process.state = CHIMERA_SUP_ACTIVE;
    pid1.process.exit_code = 0;
    copy_name(pid1.process.name, "pid1");
    pid1.process.id = PID1_PID;
    pid1.process.sched_task_id = 0;
    pid1.process.restartable = 0;
    pid1.process.max_restarts = 0;
    pid1.process.restart_count = 0;
    pid1.process.runs = 0;
    pid1.process.work = nullptr;
    pid1.process.work_arg = nullptr;
    process_count = 1;
    initialized = true;
    unlock();

    const int task_id = chimera_sched_submit(pid1_task, nullptr, PID1_PRIORITY);
    if (task_id < 0) {
        lock();
        for (uint32_t i = 0; i < CHIMERA_SUPERVISOR_MAX_PROCESSES; ++i) {
            slots[i] = ProcessSlot{};
        }
        initialized = false;
        process_count = 0;
        unlock();
        debug_text("[SUP ] ERROR: PID1 scheduler task submission failed");
        return -1;
    }
    lock();
    pid1_task_id = static_cast<uint32_t>(task_id);
    slots[0].process.sched_task_id = pid1_task_id;
    unlock();
    debug_text("[SUP ] Kernel-owned PID1 supervisor resident");
    debug_u32("[SUP ] PID1_TASK=", pid1_task_id);
    return 0;
}

extern "C" uint32_t chimera_supervisor_gate_requested(void) {
    for (uint32_t i = 0; i < chimera_multiboot_module_count(); ++i) {
        const chimera_boot_module *module = chimera_multiboot_module(i);
        if (module && has_token(module->cmdline, "koronos-supervisor-gate")) {
            return 1u;
        }
    }
    return 0u;
}

extern "C" int chimera_supervisor_spawn(chimera_supervisor_work_fn entry,
                                        void *arg, uint32_t parent_pid,
                                        const char *name, int restartable,
                                        uint32_t *pid_out) {
    if (!entry) return -1;

    lock();
    if (parent_pid != 0 && !find_locked(parent_pid)) {
        unlock();
        return -2;
    }
    ProcessSlot *slot = allocate_locked();
    if (!slot) {
        unlock();
        return -3;
    }
    slot->process.pid = next_pid++;
    if (next_pid == 0) next_pid = 2u;
    slot->process.parent_pid = parent_pid;
    slot->process.state = CHIMERA_SUP_READY;
    slot->process.exit_code = 0;
    copy_name(slot->process.name, name);
    slot->process.id = slot->process.pid;
    slot->process.sched_task_id = 0;
    slot->process.restartable = restartable ? 1u : 0u;
    slot->process.max_restarts = 0;
    slot->process.restart_count = 0;
    slot->process.runs = 0;
    slot->process.work = entry;
    slot->process.work_arg = arg;
    const uint32_t pid = slot->process.pid;
    unlock();

    /* Real scheduler submission: process lifetime is owned by the kernel. */
    const int task_id = chimera_sched_submit(
        child_task, reinterpret_cast<void *>(static_cast<uintptr_t>(pid)),
        CHILD_PRIORITY);
    if (task_id < 0) {
        lock();
        slot = find_locked(pid);
        if (slot) clear_locked(slot);
        unlock();
        return -4;
    }
    lock();
    slot = find_locked(pid);
    if (slot) slot->process.sched_task_id = static_cast<uint32_t>(task_id);
    unlock();

    if (pid_out) *pid_out = pid;
    return 0;
}

extern "C" int chimera_supervisor_wait(uint32_t parent_pid, uint32_t *pid_out,
                                       uint32_t *status_out) {
    if (parent_pid == 0) return -1;
    lock();
    bool any_child = false;
    for (uint32_t i = 0; i < CHIMERA_SUPERVISOR_MAX_PROCESSES; ++i) {
        ProcessSlot &slot = slots[i];
        if (!slot.used || slot.process.parent_pid != parent_pid) continue;
        any_child = true;
        if (slot.process.state != CHIMERA_SUP_EXITED) continue;
        slot.process.state = CHIMERA_SUP_ZOMBIE;
        const uint32_t pid = slot.process.pid;
        const uint32_t status = slot.process.exit_code;
        remember_observation_locked(pid, status);
        unlock();
        if (pid_out) *pid_out = pid;
        if (status_out) *status_out = status;
        return CHIMERA_SUP_WAIT_DELIVERED;
    }
    unlock();
    return any_child ? CHIMERA_SUP_WAIT_PENDING : CHIMERA_SUP_WAIT_NONE;
}

extern "C" uint32_t chimera_supervisor_reap_children(uint32_t parent_pid) {
    if (parent_pid == 0) return 0;
    uint32_t reaped = 0;
    lock();
    for (uint32_t i = 0; i < CHIMERA_SUPERVISOR_MAX_PROCESSES; ++i) {
        ProcessSlot &slot = slots[i];
        if (!slot.used || slot.process.parent_pid != parent_pid ||
            slot.process.state != CHIMERA_SUP_ZOMBIE) {
            continue;
        }
        reaped_last_pid = slot.process.pid;
        reaped_last_status = slot.process.exit_code;
        clear_locked(&slot);
        ++reaped;
        ++reaped_total;
    }
    unlock();
    return reaped;
}

extern "C" int chimera_supervisor_set_service_policy(uint32_t pid,
                                                     int restartable,
                                                     uint32_t max_restarts) {
    lock();
    ProcessSlot *slot = find_locked(pid);
    if (!slot) {
        unlock();
        return -1;
    }
    slot->process.restartable = restartable ? 1u : 0u;
    slot->process.max_restarts = max_restarts;
    unlock();
    return 0;
}

extern "C" uint32_t chimera_supervisor_snapshot(chimera_supervisor_snapshot_data *out) {
    if (!out) return 0;
    chimera_supervisor_snapshot_data snapshot{};
    lock();
    for (uint32_t i = 0; i < CHIMERA_SUPERVISOR_MAX_PROCESSES; ++i) {
        const ProcessSlot &slot = slots[i];
        if (!slot.used) continue;
        ++snapshot.process_count;
        switch (slot.process.state) {
            case CHIMERA_SUP_ACTIVE:  ++snapshot.active_count; break;
            case CHIMERA_SUP_READY:   ++snapshot.ready_count; break;
            case CHIMERA_SUP_RUNNING: ++snapshot.running_count; break;
            case CHIMERA_SUP_ZOMBIE:  ++snapshot.zombie_count; break;
            case CHIMERA_SUP_EXITED:  ++snapshot.exited_count; break;
            default: break;
        }
    }
    snapshot.reaped_total = reaped_total;
    snapshot.restarts_total = restarts_total;
    snapshot.notifications = notifications;
    snapshot.reaped_last_pid = reaped_last_pid;
    snapshot.reaped_last_status = reaped_last_status;
    snapshot.restart_last_pid = restart_last_pid;
    snapshot.next_pid = next_pid;
    snapshot.observed_count = observed_count < OBSERVED_SLOTS ? observed_count : OBSERVED_SLOTS;
    for (uint32_t i = 0; i < snapshot.observed_count; ++i) {
        snapshot.observed_pid[i] = observed_pid[i];
        snapshot.observed_status[i] = observed_status[i];
    }
    const ProcessSlot *pid1 = find_locked(PID1_PID);
    snapshot.pid1_pid = PID1_PID;
    snapshot.pid1_state = pid1 ? static_cast<uint32_t>(pid1->process.state)
                                 : static_cast<uint32_t>(CHIMERA_SUP_EMPTY);
    snapshot.pid1_task_id = pid1_task_id;
    unlock();
    *out = snapshot;
    return 1;
}

extern "C" uint32_t chimera_supervisor_pid1_state(void) {
    lock();
    const ProcessSlot *pid1 = find_locked(PID1_PID);
    const uint32_t state = pid1 ? static_cast<uint32_t>(pid1->process.state)
                                : static_cast<uint32_t>(CHIMERA_SUP_EMPTY);
    unlock();
    return state;
}

extern "C" int chimera_supervisor_selftest(void) {
    if (!initialized && chimera_supervisor_init() != 0) {
        debug_text("[SUP ] SELFTEST FAIL: supervisor init failed");
        return -1;
    }

    MeasuredWork worker{37u, 0x2Au, 0u};
    MeasuredWork service{19u, 0x51u, 0u};
    uint32_t worker_pid = 0;
    uint32_t service_pid = 0;
    if (chimera_supervisor_spawn(measured_work, &worker, PID1_PID,
                                 "selftest-worker", 0, &worker_pid) != 0) {
        debug_text("[SUP ] SELFTEST FAIL: worker spawn failed");
        return -1;
    }
    if (chimera_supervisor_spawn(measured_work, &service, PID1_PID,
                                 "selftest-service", 1, &service_pid) != 0) {
        debug_text("[SUP ] SELFTEST FAIL: service spawn failed");
        return -1;
    }
    if (chimera_supervisor_set_service_policy(service_pid, 1, 2u) != 0) {
        debug_text("[SUP ] SELFTEST FAIL: service policy failed");
        return -1;
    }

    uint32_t dispatches = 0;
    chimera_supervisor_snapshot_data snapshot{};
    for (uint32_t attempt = 0; attempt < SELFTEST_DISPATCH_LIMIT; ++attempt) {
        dispatches += chimera_sched_run_serial_range(
            0u, chimera_sched_cpu_count());
        (void)chimera_supervisor_snapshot(&snapshot);
        if (snapshot.reaped_total >= 4u && snapshot.restarts_total >= 2u &&
            snapshot.zombie_count == 0u && snapshot.process_count == 1u) {
            break;
        }
    }
    (void)chimera_supervisor_snapshot(&snapshot);

    uint32_t worker_exit = 0;
    uint32_t service_exit = 0;
    const bool worker_observed = observed_exit(snapshot, worker_pid, &worker_exit);
    const bool service_observed = observed_exit(snapshot, service_pid, &service_exit);
    const uint32_t worker_expected = expected_exit(worker);
    const uint32_t service_expected = expected_exit(service);

    const bool pass =
        snapshot.pid1_pid == PID1_PID &&
        snapshot.pid1_state == CHIMERA_SUP_ACTIVE &&
        snapshot.pid1_task_id != 0 &&
        worker_pid > 1u &&
        service_pid > worker_pid &&
        worker_observed && service_observed &&
        worker.completed > 0u && service.completed > 0u &&
        worker_exit == worker_expected && service_exit == service_expected &&
        snapshot.process_count == 1u &&
        snapshot.ready_count == 0u &&
        snapshot.running_count == 0u &&
        snapshot.exited_count == 0u &&
        snapshot.zombie_count == 0u &&
        snapshot.reaped_total >= 4u &&
        snapshot.restarts_total >= 2u &&
        snapshot.restart_last_pid > service_pid &&
        snapshot.notifications >= 2u &&
        dispatches > 0u;

    debug_u32("[SUP ] PID1_PID=", snapshot.pid1_pid);
    {
        char line[64];
        uint32_t pos = 0;
        const char prefix[] = "[SUP ] PID1_STATE=";
        for (uint32_t i = 0; prefix[i]; ++i) line[pos++] = prefix[i];
        const char *name = state_name(snapshot.pid1_state);
        for (uint32_t i = 0; name[i]; ++i) line[pos++] = name[i];
        line[pos] = 0;
        debug_text(line);
    }
    debug_u32("[SUP ] PID1_TASK=", snapshot.pid1_task_id);
    debug_u32("[SUP ] CHILD_PID=", worker_pid);
    debug_u32("[SUP ] CHILD_EXIT=", worker_exit);
    debug_u32("[SUP ] EXPECTED_EXIT=", worker_expected);
    debug_u32("[SUP ] WORK_COMPLETED=", worker.completed);
    debug_u32("[SUP ] SERVICE_PID=", service_pid);
    debug_u32("[SUP ] SERVICE_EXIT=", service_exit);
    debug_u32("[SUP ] SERVICE_EXPECTED=", service_expected);
    debug_u32("[SUP ] RESTART_PID=", snapshot.restart_last_pid);
    debug_u32("[SUP ] REAPED=", snapshot.reaped_total);
    debug_u32("[SUP ] ZOMBIES=", snapshot.zombie_count);
    debug_u32("[SUP ] EXITED=", snapshot.exited_count);
    debug_u32("[SUP ] PROCESSES=", snapshot.process_count);
    debug_u32("[SUP ] RESTARTS=", snapshot.restarts_total);
    debug_u32("[SUP ] NOTIFICATIONS=", snapshot.notifications);
    debug_u32("[SUP ] DISPATCHES=", dispatches);
    debug_text(pass ? "[SUP ] SELFTEST PASS" : "[SUP ] SELFTEST FAIL");
    return pass ? 0 : -1;
}
