#include <atomic>
#include <cstdint>
#include <cstdio>
#include "chimera/bootinfo.h"

namespace chimera {
class Koronos {
    std::atomic<bool> ready_{false};
public:
    void boot(const BootInfo& bi) {
        if (bi.magic != BOOTINFO_MAGIC) return;
        ready_.store(true, std::memory_order_release);
        std::puts("KORONOS_READY");
    }
    bool ready() const noexcept { return ready_.load(std::memory_order_acquire); }
};
}
