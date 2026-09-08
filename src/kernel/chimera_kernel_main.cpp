#include "chimera/kernel_arch.hpp"

#include <atomic>
#include <chrono>
#include <csignal>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <string>
#include <thread>

namespace {
std::atomic_bool running{true};

void stop_handler(int) noexcept { running.store(false, std::memory_order_relaxed); }

std::string runtime_dir() {
    if (const char* dir = std::getenv("CHIMERA_RUNTIME_DIR"); dir && *dir) return dir;
    return "/run/chimera";
}

bool write_ready_file(const std::string& dir) {
    std::error_code ec;
    std::filesystem::create_directories(dir, ec);
    if (ec) return false;
    std::ofstream out(dir + "/kernel.ready", std::ios::trunc);
    if (!out) return false;
    out << "chimera-kernel=userspace-runtime\n"
        << "abi=stable\n"
        << "scheduler=enabled\n"
        << "vm=enabled\n";
    return true;
}

void remove_ready_file(const std::string& dir) noexcept {
    std::error_code ec;
    std::filesystem::remove(dir + "/kernel.ready", ec);
}
}

int main() {
    std::signal(SIGINT, stop_handler);
    std::signal(SIGTERM, stop_handler);

    chimera::kernel::Kernel kernel;
    kernel.init();

    const std::string dir = runtime_dir();
    if (!write_ready_file(dir)) {
        std::fprintf(stderr, "chimera-kernel: unable to create readiness marker in %s\n", dir.c_str());
        return EXIT_FAILURE;
    }

    std::fprintf(stdout, "chimera-kernel: initialized; entering scheduler loop\n");
    std::fflush(stdout);

    while (running.load(std::memory_order_relaxed)) {
        kernel.schedule();
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    remove_ready_file(dir);
    std::fprintf(stdout, "chimera-kernel: shutting down\n");
    return EXIT_SUCCESS;
}
