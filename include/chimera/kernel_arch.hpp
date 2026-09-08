#pragma once
#include <array>
#include <cstdint>
#include <cstddef>
namespace chimera::kernel {
enum class TaskState : std::uint32_t { Ready=0, Running=1, Blocked=2, Sleeping=3, Terminated=4 };
struct Task { std::uint64_t id{}, stack{}, address_space{}; std::uint32_t priority{}; TaskState state{TaskState::Ready}; std::uint64_t vruntime{}; };
struct CpuContext { std::uint64_t pc{}, sp{}, flags{}; std::array<std::uint64_t,32> gpr{}; };
struct Page { std::uint64_t phys{}, flags{}; };
struct VmRegion { std::uint64_t start{}, end{}, physical{}, prot{}; };
struct PacketView { const void* data{}; std::size_t length{}; std::uint32_t protocol{}; };
struct FileHandle { std::uint64_t inode{}, offset{}; std::uint32_t flags{}; };
class Scheduler {
public:
    static constexpr std::size_t kMaxTasks=256;
    void enqueue(Task*); Task* pick_next(); void tick(); void yield(Task*); void block(Task*); void wake(Task*);
    [[nodiscard]] std::uint64_t ticks() const noexcept { return ticks_; }
private:
    std::array<Task*,kMaxTasks> queue_{}; std::size_t count_{}; std::uint64_t ticks_{};
    [[nodiscard]] bool contains(const Task*) const noexcept;
};
class MemoryManager {
public:
    static constexpr std::uint64_t kPageSize=4096; static constexpr std::size_t kMaxMappings=256;
    void* alloc_page(); void free_page(void*);
    bool map(std::uint64_t virtual_address,std::uint64_t physical_address,std::uint64_t flags);
    bool unmap(std::uint64_t virtual_address);
    [[nodiscard]] bool is_mapped(std::uint64_t virtual_address) const noexcept;
    [[nodiscard]] bool validate_range(std::uint64_t address,std::uint64_t length) const noexcept;
private:
    std::array<VmRegion,kMaxMappings> mappings_{}; std::size_t mapping_count_{};
};
class Kernel {
public:
    void init(); void schedule(); void handle_irq(std::uint32_t);
    long syscall(std::uint64_t,std::uint64_t,std::uint64_t,std::uint64_t,std::uint64_t,std::uint64_t);
    [[nodiscard]] Scheduler& scheduler() noexcept { return scheduler_; }
    [[nodiscard]] MemoryManager& memory() noexcept { return memory_; }
private: Scheduler scheduler_; MemoryManager memory_;
};
}
