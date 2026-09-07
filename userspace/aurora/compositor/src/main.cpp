#include "aurora/compositor.hpp"

#include <iostream>

int main() {
    aurora::AuroraCompositor compositor;
    if (!compositor.init()) {
        std::cerr << "Aurora initialization failed.\n";
        return 1;
    }

    return compositor.run();
}
