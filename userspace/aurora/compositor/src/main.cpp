#include "aurora/compositor.hpp"

#include <csignal>
#include <iostream>

namespace {
volatile std::sig_atomic_t g_stop = 0;

void handle_signal(int) noexcept { g_stop = 1; }
} // namespace

int main() {
    std::signal(SIGINT, handle_signal);
    std::signal(SIGTERM, handle_signal);

    aurora::AuroraCompositor compositor;
    if (!compositor.init()) {
        std::cerr << "Aurora initialization failed.\n";
        return 1;
    }

    return compositor.run();
}
