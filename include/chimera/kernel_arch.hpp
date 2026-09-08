#pragma once
#include <cstdint>
#include <cstddef>
#include <array>
namespace chimera::kernel {
struct Task { uint64_t id{}, stack{}, address_space{}; uint32_t priority{}; uint32_t state{}; };
struct CpuContext { uint64_t pc{}, sp{}, flags{}; std::array<uint64_t,32> gpr{}; };
struct Page { uint64_t phys{}, flags{}; };
struct VmRegion { uint64_t start{}, end{}, prot{}, flags{}; };
struct PacketView { const void* data{}; std::size_t length{}; uint32_t protocol{}; };
struct FileHandle { uint64_t inode{}, offset{}; uint32_t flags{}; };
class Scheduler { public: void enqueue(Task*); Task* pick_next(); void tick(); private: std::array<Task*,256> queue_{}; std::size_t count_{}; };
class MemoryManager { public: void* alloc_page(); void free_page(void*); bool map(uint64_t,uint64_t,uint64_t); };
class Kernel { public: void init(); void schedule(); void handle_irq(uint32_t); long syscall(uint64_t,uint64_t,uint64_t,uint64_t,uint64_t,uint64_t); private: Scheduler scheduler_; MemoryManager memory_; };
}
