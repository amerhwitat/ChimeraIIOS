#include <cstdio>

extern "C" int aurora_media_open(const char* path) {
    if (!path || !*path) return 2;
    std::printf("Aurora Media Player: open %s\n", path);
    return 0;
}

int main(int argc, char** argv) {
    return aurora_media_open(argc > 1 ? argv[1] : nullptr);
}
