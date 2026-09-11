#pragma once
#include <cstdint>

namespace chimera::mobile {

enum class MobileArchitecture : std::uint8_t {
    Unknown,
    AArch64,
    RiscV64
};

class PlatformContract {
public:
    constexpr MobileArchitecture architecture() const noexcept { return architecture_; }
    constexpr std::uint32_t page_size() const noexcept { return page_size_; }
    constexpr std::uint32_t cpu_count() const noexcept { return cpu_count_; }

    constexpr void set_architecture(MobileArchitecture value) noexcept { architecture_ = value; }
    constexpr void set_page_size(std::uint32_t value) noexcept { page_size_ = value; }
    constexpr void set_cpu_count(std::uint32_t value) noexcept { cpu_count_ = value; }

    constexpr bool has_required_memory(std::uint64_t bytes) const noexcept {
        return bytes >= minimum_memory_bytes;
    }

    constexpr bool valid() const noexcept {
        return architecture_ != MobileArchitecture::Unknown &&
               page_size_ != 0 && cpu_count_ != 0;
    }

    static constexpr std::uint64_t minimum_memory_bytes = 64ull * 1024ull * 1024ull;

private:
    MobileArchitecture architecture_{MobileArchitecture::Unknown};
    std::uint32_t page_size_{4096};
    std::uint32_t cpu_count_{};
};

} // namespace chimera::mobile
