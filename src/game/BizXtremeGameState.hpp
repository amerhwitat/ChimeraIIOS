#pragma once

#include <cstdint>
#include <string>

namespace chimera::bizx {

struct GameState {
    std::uint32_t schema = 1;
    std::string chapter = "chapter_01";
    std::uint64_t score = 0;
    std::uint64_t xp = 0;
    double expedition = 0.0;
    double play_time_seconds = 0.0;
    std::string saved_at_utc;
};

// Stable field vocabulary shared with the Three.js and Unity save contracts.
struct DashboardKpis {
    std::uint64_t score = 0;
    std::uint64_t xp = 0;
    double expedition = 0.0;
    double play_time_seconds = 0.0;
    std::uint32_t peer_count = 0;
    std::int32_t rank = -1;
};

} // namespace chimera::bizx
