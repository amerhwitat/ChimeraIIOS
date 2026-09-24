#include <cstdio>
#ifdef _WIN32
#include <cstdlib>
#else
#include <unistd.h>
#endif

extern "C" int aurora_media_open(const char* path) {
    if (!path || !*path) return 2;
#ifdef _WIN32
    std::printf("Aurora Media Player: %s\n", path);
    return 0;
#else
    char* const args[] = {
        const_cast<char*>("aurora_media_player.py"),
        const_cast<char*>(path),
        nullptr
    };
    ::execvp(args[0], args);
    std::perror("Aurora Media Player: unable to start playback provider");
    return 127;
#endif
}

int main(int argc, char** argv) {
    return aurora_media_open(argc > 1 ? argv[1] : nullptr);
}
