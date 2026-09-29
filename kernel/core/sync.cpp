#include "chimera/sync.h"
#include "chimera/timer.h"

namespace {
volatile uint32_t global_lock = 0;
static void lock() { while (__sync_lock_test_and_set(&global_lock, 1u)) {} }
static void unlock() { __sync_lock_release(&global_lock); }

static int current_id(chimera_thread_id *id) {
    return chimera_thread_current(id) == 0 ? 0 : -1;
}

static void wake_one(chimera_waitable *o) {
    for (uint32_t i = 0; i < CHIMERA_SYNC_MAX_WAITERS; ++i) {
        if (o->waiters[i].active) {
            chimera_thread_wake(o->waiters[i].thread_id);
            o->waiters[i].active = 0;
            break;
        }
    }
}
static void wake_all(chimera_waitable *o) {
    for (uint32_t i = 0; i < CHIMERA_SYNC_MAX_WAITERS; ++i) {
        if (o->waiters[i].active) {
            chimera_thread_wake(o->waiters[i].thread_id);
            o->waiters[i].active = 0;
        }
    }
}
static int consume(chimera_waitable *o, chimera_thread_id tid) {
    if (o->type == CHIMERA_WAITABLE_EVENT) {
        if (!o->signaled) return 0;
        if (!o->manual_reset) o->signaled = 0;
        return 1;
    }
    if (o->type == CHIMERA_WAITABLE_MUTEX) {
        if (o->owner_thread == 0) {
            o->owner_thread = tid; o->recursion = 1; return 1;
        }
        if (o->owner_thread == tid) {
            ++o->recursion; return 1;
        }
        return 0;
    }
    if (o->count != 0) {
        --o->count;
        return 1;
    }
    return 0;
}
static int register_waiter(chimera_waitable *o, chimera_thread_id tid, uint64_t deadline) {
    for (uint32_t i=0;i<CHIMERA_SYNC_MAX_WAITERS;++i)
        if (o->waiters[i].active && o->waiters[i].thread_id == tid) return 0;
    for (uint32_t i=0;i<CHIMERA_SYNC_MAX_WAITERS;++i) {
        if (!o->waiters[i].active) {
            o->waiters[i].thread_id = tid;
            o->waiters[i].active = 1;
            o->waiters[i].deadline_tick = deadline;
            return 0;
        }
    }
    return -2;
}
}

extern "C" void chimera_event_init(chimera_waitable *e, uint32_t manual, uint32_t initial) {
    if (!e) return;
    *e = {};
    e->type = CHIMERA_WAITABLE_EVENT;
    e->manual_reset = manual ? 1u : 0u;
    e->signaled = initial ? 1u : 0u;
}
extern "C" int chimera_event_set(chimera_waitable *e) {
    if (!e || e->type != CHIMERA_WAITABLE_EVENT) return -1;
    lock(); e->signaled = 1;
    if (e->manual_reset) wake_all(e); else wake_one(e);
    unlock(); return 0;
}
extern "C" int chimera_event_reset(chimera_waitable *e) {
    if (!e || e->type != CHIMERA_WAITABLE_EVENT) return -1;
    lock(); e->signaled = 0; unlock(); return 0;
}
extern "C" int chimera_mutex_init(chimera_waitable *m) {
    if (!m) return -1; *m = {}; m->type = CHIMERA_WAITABLE_MUTEX; return 0;
}
extern "C" int chimera_mutex_release(chimera_waitable *m) {
    if (!m || m->type != CHIMERA_WAITABLE_MUTEX) return -1;
    chimera_thread_id tid; if (current_id(&tid) != 0) return -2;
    lock();
    if (m->owner_thread != tid) { unlock(); return -3; }
    if (m->recursion > 1) --m->recursion;
    else { m->owner_thread = 0; m->recursion = 0; wake_one(m); }
    unlock(); return 0;
}
extern "C" int chimera_semaphore_init(chimera_waitable *s, uint32_t initial, uint32_t maximum) {
    if (!s || maximum == 0 || initial > maximum) return -1;
    *s = {}; s->type = CHIMERA_WAITABLE_SEMAPHORE; s->count = initial; s->limit = maximum; return 0;
}
extern "C" int chimera_semaphore_release(chimera_waitable *s, uint32_t n, uint32_t *previous) {
    if (!s || s->type != CHIMERA_WAITABLE_SEMAPHORE || n == 0) return -1;
    lock();
    if (s->count > s->limit - n) { unlock(); return -2; }
    if (previous) *previous = s->count;
    s->count += n;
    for (uint32_t i=0;i<n;++i) wake_one(s);
    unlock(); return 0;
}
extern "C" chimera_wait_result chimera_wait_one(chimera_waitable *o, uint32_t timeout, uint32_t alertable) {
    if (!o) return CHIMERA_WAIT_FAILED;
    chimera_thread_id tid = 0;
    if (o->type == CHIMERA_WAITABLE_MUTEX && current_id(&tid) != 0) return CHIMERA_WAIT_FAILED;
    lock();
    if (consume(o, tid)) { unlock(); return CHIMERA_WAIT_SIGNALED; }
    if (timeout == 0) { unlock(); return CHIMERA_WAIT_TIMEOUT; }
    if (tid == 0 || register_waiter(o, tid, timeout == CHIMERA_WAIT_INFINITE ? UINT64_MAX : chimera_timer_now() + timeout) != 0) { unlock(); return CHIMERA_WAIT_FAILED; }
    unlock();
    chimera_thread_block();
    (void)alertable;
    return CHIMERA_WAIT_BLOCKED;
}
extern "C" chimera_wait_result chimera_wait_register(chimera_waitable *o, uint32_t timeout, uint32_t alertable) {
    return chimera_wait_one(o, timeout, alertable);
}
extern "C" int chimera_wait_cancel(chimera_waitable *o, chimera_thread_id tid) {
    if (!o || tid == 0) return -1;
    lock();
    for (uint32_t i=0;i<CHIMERA_SYNC_MAX_WAITERS;++i)
        if (o->waiters[i].active && o->waiters[i].thread_id == tid) {
            o->waiters[i].active = 0; unlock(); return 0;
        }
    unlock(); return -2;
}
extern "C" uint32_t chimera_waiter_count(const chimera_waitable *o) {
    if (!o) return 0; uint32_t n=0;
    for (uint32_t i=0;i<CHIMERA_SYNC_MAX_WAITERS;++i) n += o->waiters[i].active ? 1u : 0u;
    return n;
}

extern "C" void chimera_wait_tick(uint64_t now_tick) {
    lock();
    for (uint32_t i = 0; i < 1024; ++i) {
        (void)i;
    }
    unlock();
}
