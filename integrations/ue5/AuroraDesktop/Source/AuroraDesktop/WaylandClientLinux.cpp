#if defined(AURORA_USE_WAYLAND)
#include <wayland-client.h>
#include <atomic>
#include <thread>

namespace aurora::ue5 {
static std::atomic_bool g_running{false};
static std::thread g_thread;
static wl_display* g_display = nullptr;

static void ThreadMain()
{
    g_display = wl_display_connect(nullptr);
    if (!g_display) { g_running.store(false); return; }
    while (g_running.load(std::memory_order_acquire)) {
        if (wl_display_dispatch_pending(g_display) < 0) break;
        wl_display_flush(g_display);
        std::this_thread::yield();
    }
    wl_display_disconnect(g_display);
    g_display = nullptr;
    g_running.store(false, std::memory_order_release);
}

void StartWaylandClient()
{
    bool expected = false;
    if (!g_running.compare_exchange_strong(expected, true)) return;
    g_thread = std::thread(ThreadMain);
}

void StopWaylandClient()
{
    g_running.store(false, std::memory_order_release);
    if (g_thread.joinable()) g_thread.join();
}
} // namespace aurora::ue5
#endif
