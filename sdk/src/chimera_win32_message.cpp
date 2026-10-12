#include "chimera/win32_message.h"

#include <cstring>

namespace {
thread_local chm_event_queue *g_queue = nullptr;
}
extern "C" int chm_win32_bind_message_queue(chm_event_queue *queue) {
    g_queue = queue;
    return queue ? 0 : -1;
}
extern "C" int chm_win32_post_message(chm_hwnd hwnd, uint32_t message,
                                       chm_wparam wParam, chm_lparam lParam) {
    if (!g_queue || message == CHM_WM_QUIT) return -1;
    chm_event e{};
    e.size = sizeof(e);
    e.type = CHM_EVENT_USER;
    e.target = hwnd;
    e.value1 = static_cast<int64_t>(message);
    e.value2 = static_cast<int64_t>(wParam);
    e.payload = static_cast<uintptr_t>(lParam);
    return chm_event_post(g_queue, &e);
}
extern "C" int chm_win32_post_quit_message(int exit_code) {
    if (!g_queue) return -1;
    chm_event e{};
    e.size = sizeof(e);
    e.type = CHM_EVENT_QUIT;
    e.value1 = exit_code;
    return chm_event_post(g_queue, &e);
}
static int read_message(chm_win32_msg *out, uint32_t timeout_ms) {
    if (!g_queue || !out) return -1;
    chm_event e{};
    const int rc = chm_event_next(g_queue, &e, timeout_ms);
    if (rc < 0) return -1;
    if (rc == 0) return 2; /* timeout/no message, distinct from WM_QUIT */
    std::memset(out, 0, sizeof(*out));
    out->hwnd = e.target;
    out->time_ns = e.timestamp_ns;
    if (e.type == CHM_EVENT_QUIT) {
        out->message = CHM_WM_QUIT;
        out->wParam = static_cast<chm_wparam>(e.value1);
        return 0;
    }
    out->message = static_cast<uint32_t>(e.value1);
    out->wParam = static_cast<chm_wparam>(e.value2);
    out->lParam = static_cast<chm_lparam>(e.payload);
    return 1;
}
extern "C" int chm_win32_get_message(chm_win32_msg *out, uint32_t timeout_ms) {
    return read_message(out, timeout_ms);
}
extern "C" int chm_win32_peek_message(chm_win32_msg *out) {
    const int rc = read_message(out, 0);
    return rc == 2 ? 0 : rc;
}
extern "C" int chm_win32_dispatch_message(const chm_win32_msg *message,
                                            chm_win32_wndproc procedure, void *context) {
    if (!message || !procedure || message->message == CHM_WM_QUIT) return -1;
    procedure(message, context);
    return 0;
}
