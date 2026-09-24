#include <cstdio>
#ifdef _WIN32
#include <cstdlib>
#else
#include <unistd.h>
#endif

extern "C" int aurora_video_open(const char* path) {
    if (!path || !*path) return 2;
#ifdef _WIN32
    std::printf("Aurora Video Player: %s\n", path);
    return 0;
#else
    char* const args[] = {
        const_cast<char*>("aurora_video_player.py"),
        const_cast<char*>(path),
        nullptr
    };
    ::execvp(args[0], args);
    std::perror("Aurora Video Player: unable to start playback provider");
    return 127;
#endif
}

int main(int argc, char** argv) {
    return aurora_video_open(argc > 1 ? argv[1] : nullptr);
}
