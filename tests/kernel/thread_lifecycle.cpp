#include <cassert>
#include <cstdint>
#include "chimera/thread.h"

static uint32_t runs = 0;
static void worker(void *) { ++runs; chimera_thread_yield(); }

int main() {
    chimera_sched_init(2);
    chimera_thread_id id = 0;
    assert(chimera_thread_create(worker, nullptr, 10, 0xffffffffu, &id) == 0);
    assert(id != 0);
    assert(chimera_sched_runnable_count() == 1);
    assert(chimera_sched_run_once(0) == 1);
    assert(runs == 1);
    assert(chimera_sched_run_once(1) == 1);
    assert(runs == 2);
    assert(chimera_thread_wake(id) == 0);
    return 0;
}
