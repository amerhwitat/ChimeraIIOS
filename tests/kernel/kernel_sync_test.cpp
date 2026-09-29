#include <assert.h>
#include <stdint.h>
#include "chimera/scheduler.h"
#include "chimera/thread.h"
#include "chimera/sync.h"
#include "chimera/timer.h"
#include "chimera/apc.h"
#include "chimera/dpc.h"

static chimera_waitable event_obj;
static uint32_t task_runs;
static chimera_wait_result last_wait;
static uint32_t timer_hits, apc_hits, dpc_hits;
static chimera_waitable mutex_obj;
static chimera_waitable timeout_event;
static uint32_t timeout_runs;
static chimera_wait_result timeout_result;

static void wait_task(void*) {
    ++task_runs;
    last_wait = chimera_wait_one(&event_obj, task_runs == 1 ? 1u : 0u, 1u);
    if (task_runs == 2) {
        assert(chimera_mutex_init(&mutex_obj) == 0);
        assert(chimera_wait_one(&mutex_obj, 0, 0) == CHIMERA_WAIT_SIGNALED);
        assert(chimera_wait_one(&mutex_obj, 0, 0) == CHIMERA_WAIT_SIGNALED);
        assert(chimera_mutex_release(&mutex_obj) == 0);
        assert(chimera_mutex_release(&mutex_obj) == 0);
    }
}

static void timer_cb(chimera_timer_id, void*) { ++timer_hits; }
static void timeout_task(void*) {
    ++timeout_runs;
    timeout_result = chimera_wait_one(&timeout_event, timeout_runs == 1 ? 2u : 0u, 0);
}
static void apc_cb(chimera_thread_id, void*) { ++apc_hits; }
static void dpc_cb(chimera_dpc_id, void*) { ++dpc_hits; }

int main() {
    chimera_sched_init(1);
    chimera_event_init(&event_obj, 0, 0);

    chimera_thread_id tid = 0;
    assert(chimera_thread_create(wait_task, nullptr, 8, 1, &tid) == 0);
    assert(chimera_sched_run_once(0) == 1);
    assert(last_wait == CHIMERA_WAIT_BLOCKED);
    assert(chimera_waiter_count(&event_obj) == 1);

    assert(chimera_event_set(&event_obj) == 0);
    assert(chimera_sched_run_once(0) == 1);
    assert(last_wait == CHIMERA_WAIT_SIGNALED);

    chimera_waitable sem;
    uint32_t previous = 0;
    assert(chimera_semaphore_init(&sem, 0, 2) == 0);
    assert(chimera_semaphore_release(&sem, 1, &previous) == 0 && previous == 0);
    assert(chimera_wait_one(&sem, 0, 0) == CHIMERA_WAIT_SIGNALED);
    assert(chimera_wait_one(&sem, 0, 0) == CHIMERA_WAIT_TIMEOUT);

    assert(chimera_timer_init() == 0);
    chimera_timer_id timer = 0;
    assert(chimera_timer_create(2, 0, timer_cb, nullptr, &timer) == 0);
    assert(chimera_timer_tick(1) == 0);
    assert(timer_hits == 0);

    chimera_event_init(&timeout_event, 0, 0);
    chimera_thread_id timeout_tid = 0;
    assert(chimera_thread_create(timeout_task, nullptr, 8, 1, &timeout_tid) == 0);
    assert(chimera_sched_run_once(0) == 1);
    assert(timeout_result == CHIMERA_WAIT_BLOCKED);
    assert(chimera_timer_tick(1) == 0);
    assert(chimera_timer_tick(1) == 1);
    assert(chimera_sched_run_once(0) >= 1);
    assert(timeout_result == CHIMERA_WAIT_TIMEOUT);
    assert(chimera_timer_tick(1) == 1);
    assert(timer_hits == 1);
    assert(chimera_timer_active_count() == 0);

    assert(chimera_apc_queue(tid, apc_cb, nullptr) == 0);
    assert(chimera_apc_pending(tid) == 1);
    assert(chimera_apc_deliver(tid, 1, 8) == 1);
    assert(apc_hits == 1);

    assert(chimera_dpc_init() == 0);
    chimera_dpc_id dpc = 0;
    assert(chimera_dpc_queue(dpc_cb, nullptr, &dpc) == 0);
    assert(chimera_dpc_pending() == 1);
    assert(chimera_dpc_run(8) == 1);
    assert(dpc_hits == 1);

    return 0;
}
