#include "chimera/thread.h"

extern "C" int chimera_thread_create(chimera_task_fn entry, void *argument,
                                      uint32_t priority, uint32_t affinity_mask,
                                      chimera_thread_id *out_id) {
    if (!entry || !out_id) return -1;
    int id = chimera_sched_submit(entry, argument, priority);
    if (id < 0) return id;
    *out_id = (chimera_thread_id)id;
    (void)affinity_mask;
    return 0;
}

extern "C" int chimera_thread_exit(void) {
    chimera_sched_exit();
    return 0;
}

extern "C" int chimera_thread_yield(void) {
    chimera_sched_yield();
    return 0;
}

extern "C" int chimera_thread_block(void) {
    chimera_sched_block();
    return 0;
}

extern "C" int chimera_thread_wake(chimera_thread_id id) {
    chimera_sched_wake(id);
    return 0;
}

extern "C" int chimera_thread_current(chimera_thread_id *out_id) {
    if (!out_id) return -1;
    chimera_task_info snapshot[1024];
    uint32_t n = chimera_sched_snapshot(snapshot, 1024);
    for (uint32_t i = 0; i < n; ++i) {
        if (snapshot[i].state == CHIMERA_TASK_RUNNING) {
            *out_id = snapshot[i].id;
            return 0;
        }
    }
    return -2;
}

extern "C" uint32_t chimera_thread_snapshot(chimera_thread_info *out,
                                              uint32_t capacity) {
    if (!out || capacity == 0) return 0;
    chimera_task_info snapshot[1024];
    uint32_t n = chimera_sched_snapshot(snapshot, 1024);
    if (n > capacity) n = capacity;
    for (uint32_t i = 0; i < n; ++i) {
        out[i].id = snapshot[i].id;
        out[i].priority = snapshot[i].priority;
        out[i].cpu = snapshot[i].cpu;
        out[i].state = snapshot[i].state;
        out[i].affinity_mask = 0;
        out[i].runs = snapshot[i].runs;
        out[i].ticks = snapshot[i].ticks;
        out[i].argument = 0;
    }
    return n;
}
