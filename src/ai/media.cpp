#include "chimera/ai/media.h"
#include <algorithm>
#include <cctype>

namespace chimera::ai::media {
static std::string normalize(std::string_view s) {
    std::string out; out.reserve(s.size());
    bool space = false;
    for (unsigned char c : s) {
        if (std::isspace(c)) { if (!out.empty()) space = true; continue; }
        if (space) { out.push_back(' '); space = false; }
        out.push_back(static_cast<char>(std::tolower(c)));
    }
    return out;
}
VoiceCommand parse_voice_command(std::string_view text) {
    const auto n = normalize(text);
    const std::pair<const char*, const char*> table[] = {
        {"start recording", "record_start"}, {"stop recording", "record_stop"},
        {"play audio", "play"}, {"pause audio", "pause"}, {"open camera", "camera_start"},
        {"close camera", "camera_stop"}, {"take photo", "snapshot"}, {"scan camera", "vision_scan"}
    };
    for (const auto& [phrase, action] : table) if (n.find(phrase) != std::string::npos) return {std::string(text), action, true};
    return {std::string(text), {}, false};
}
}
