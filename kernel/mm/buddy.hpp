#pragma once
#include <cstddef>
#include <cstdint>
namespace chimera {
struct Frame { std::uintptr_t base=0; std::size_t size=0; bool free=true; };
class BuddyAllocator {
    std::uintptr_t base_; std::size_t size_;
public:
    BuddyAllocator(std::uintptr_t base,std::size_t size):base_(base),size_(size){}
    Frame reserve(std::size_t bytes) noexcept { return {base_, bytes, false}; }
    std::uintptr_t base() const noexcept { return base_; }
    std::size_t size() const noexcept { return size_; }
};
}
