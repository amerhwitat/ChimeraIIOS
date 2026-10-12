#include "chimera/event.h"

#include <chrono>
#include <condition_variable>
#include <deque>
#include <mutex>
#include <new>

struct chm_event_queue {
    explicit chm_event_queue(size_t limit) : capacity(limit) {}
    const size_t capacity;
    std::mutex mutex;
    std::condition_variable ready;
    std::deque<chm_event> events;
    bool stopped = false;
};

static uint64_t now_ns() {
    using clock = std::chrono::steady_clock;
    return static_cast<uint64_t>(
        std::chrono::duration_cast<std::chrono::nanoseconds>(
            clock::now().time_since_epoch()).count());
}

extern "C" chm_event_queue *chm_event_queue_create(size_t capacity) {
    if (!capacity || capacity > 65536) return nullptr;
    try { return new (std::nothrow) chm_event_queue(capacity); }
    catch (...) { return nullptr; }
}
extern "C" void chm_event_queue_destroy(chm_event_queue *q) { delete q; }
extern "C" int chm_event_post(chm_event_queue *q, const chm_event *event) {
    if (!q || !event || event->size < sizeof(chm_event)) return -1;
    std::lock_guard<std::mutex> lock(q->mutex);
    if (q->stopped || q->events.size() >= q->capacity) return -2;
    chm_event copy = *event;
    if (!copy.timestamp_ns) copy.timestamp_ns = now_ns();
    try { q->events.push_back(copy); }
    catch (...) { return -3; }
    q->ready.notify_one();
    return 0;
}
extern "C" int chm_event_next(chm_event_queue *q, chm_event *out, uint32_t timeout_ms) {
    if (!q || !out) return -1;
    std::unique_lock<std::mutex> lock(q->mutex);
    auto predicate = [&] { return q->stopped || !q->events.empty(); };
    if (timeout_ms == UINT32_MAX) q->ready.wait(lock, predicate);
    else if (timeout_ms != 0 &&
             !q->ready.wait_for(lock, std::chrono::milliseconds(timeout_ms), predicate))
        return 0;
    if (q->events.empty()) return q->stopped ? -1 : 0;
    *out = q->events.front();
    q->events.pop_front();
    return 1;
}
extern "C" int chm_event_run(chm_event_queue *q, chm_event_handler handler,
                              void *context, uint32_t idle_timeout_ms) {
    if (!q || !handler) return -1;
    chm_event event{};
    for (;;) {
        const int rc = chm_event_next(q, &event, idle_timeout_ms);
        if (rc < 0) return 0;
        if (rc == 0) continue;
        handler(&event, context);
        if (event.type == CHM_EVENT_QUIT) return 0;
    }
}
extern "C" void chm_event_stop(chm_event_queue *q) {
    if (!q) return;
    std::lock_guard<std::mutex> lock(q->mutex);
    q->stopped = true;
    q->ready.notify_all();
}
extern "C" int CHM_PostMessage(chm_event_queue *q, chm_handle target,
                                uint32_t type, int64_t a, int64_t b) {
    chm_event e{};
    e.size = sizeof(e); e.type = type; e.target = target;
    e.value1 = a; e.value2 = b;
    return chm_event_post(q, &e);
}
extern "C" int CHM_GetMessage(chm_event_queue *q, CHM_MSG *out, uint32_t timeout_ms) {
    return chm_event_next(q, out, timeout_ms);
}
extern "C" int CHM_DispatchMessage(const CHM_MSG *message,
                                    chm_event_handler handler, void *context) {
    if (!message || !handler) return -1;
    handler(message, context);
    return 0;
}
