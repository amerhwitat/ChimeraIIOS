#include "chimera/ai/media.h"
#include <cassert>
int main() {
    auto a = chimera::ai::media::parse_voice_command("Open Camera");
    assert(a.action == "camera_start" && a.requires_confirmation);
    auto b = chimera::ai::media::parse_voice_command("hello there");
    assert(b.action.empty() && !b.requires_confirmation);
    return 0;
}
