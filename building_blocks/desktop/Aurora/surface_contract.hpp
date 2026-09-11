#pragma once
#include <cstdint>

namespace chimera::aurora {

enum class SurfaceFormat : std::uint8_t { RGBA8, BGRA8, RGB10A2, RGBA16F };

struct Surface {
    std::uint32_t width{};
    std::uint32_t height{};
    std::uint32_t stride{};
    SurfaceFormat format{SurfaceFormat::RGBA8};
    std::uint64_t buffer_id{};
};

struct PresentRequest {
    std::uint64_t surface_id{};
    std::uint64_t frame_id{};
    std::uint64_t target_time_ns{};
};

constexpr bool valid(const Surface& s) noexcept {
    return s.width != 0 && s.height != 0 && s.stride >= s.width && s.buffer_id != 0;
}

} // namespace chimera::aurora
