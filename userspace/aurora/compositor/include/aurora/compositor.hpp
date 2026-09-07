#pragma once

#include <memory>

namespace aurora {

class AuroraCompositor {
public:
    AuroraCompositor();
    ~AuroraCompositor();

    AuroraCompositor(const AuroraCompositor&) = delete;
    AuroraCompositor& operator=(const AuroraCompositor&) = delete;

    bool init();
    int run();
    void shutdown() noexcept;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

} // namespace aurora
