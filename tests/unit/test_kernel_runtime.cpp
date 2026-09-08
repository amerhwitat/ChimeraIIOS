#include "chimera/kernel_arch.hpp"
#include "chimera/bootinfo.hpp"
#include <cassert>
#include <cstdint>
#include <cstring>

int main() {
    using namespace chimera::kernel;

    Scheduler scheduler;
    Task low{1, 0, 0, 10, TaskState::Ready};
    Task high{2, 0, 0, 100, TaskState::Ready};
    scheduler.enqueue(&low);
    scheduler.enqueue(&high);
    Task* first = scheduler.pick_next();
    assert(first == &high);
    assert(first->state == TaskState::Running);
    scheduler.yield(first);
    assert(first->state == TaskState::Ready);

    MemoryManager memory;
    void* page = memory.alloc_page();
    assert(page != nullptr);
    std::memset(page, 0xA5, 4096);
    assert(memory.map(0x2000, 0x9000, 0x3));
    assert(memory.is_mapped(0x2000));
    assert(!memory.map(0x2000, 0xA000, 0x3));
    assert(memory.unmap(0x2000));
    assert(!memory.is_mapped(0x2000));
    memory.free_page(page);

    chimera::boot::BootInfo info{};
    info.magic = chimera::boot::kBootMagic;
    info.version = chimera::boot::kBootVersion;
    info.size = sizeof(info);
    info.memory_map_count = 1;
    info.memory_map[0] = {0x100000, 0x400000, chimera::boot::MemoryType::Usable, 0};
    info.finalize_crc();
    assert(info.valid());
    info.memory_map[0].length++;
    assert(!info.valid());
    return 0;
}
