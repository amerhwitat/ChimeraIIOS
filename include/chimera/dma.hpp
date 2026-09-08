#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
namespace chimera::dma {
enum class Direction : std::uint8_t { ToDevice, FromDevice, Bidirectional };
struct Device { std::uint32_t id{}; std::uint64_t dma_mask{~0ULL}; };
struct Buffer { void* address{}; std::size_t size{}; std::size_t alignment{}; explicit operator bool()const noexcept{return address!=nullptr;} };
struct Token { std::uint64_t id{}; bool valid()const noexcept{return id!=0;} };
struct Mapping { Token token{}; Device device{}; Buffer buffer{}; Direction direction{}; std::uint64_t dma_address{}; bool synced{}; };
class Manager {
public:
    static constexpr std::size_t kMaxMappings=256;
    Buffer allocate(std::size_t bytes,std::size_t alignment=4096);
    void release(Buffer buffer) noexcept;
    Token map(const Device&,Buffer,Direction);
    bool sync(Token) noexcept;
    bool unmap(Token) noexcept;
    std::optional<Mapping> lookup(Token) const;
private:
    std::array<std::optional<Mapping>,kMaxMappings> mappings_{}; std::uint64_t next_token_{1};
};
}
