#include <cstdio>

extern "C" int aurora_video_open(const char* path) {
    if (!path || !*path) return 2;
    std::printf("Aurora Video Player: open %s\n", path);
    return 0;
}

int main(int argc, char** argv) {
    return aurora_video_open(argc > 1 ? argv[1] : nullptr);
}
