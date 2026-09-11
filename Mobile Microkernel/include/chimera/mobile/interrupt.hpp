#pragma once
#include <cstdint>

namespace chimera::mobile {

using InterruptId = std::uint32_t;
using InterruptHandler = void (*)(InterruptId, void*);

class InterruptController {
public:
    bool register_handler(InterruptId id, InterruptHandler handler, void* context) noexcept {
        return id != 0 && handler != nullptr && context != nullptr;
    }

    void acknowledge(InterruptId) noexcept {}
    void end_of_interrupt(InterruptId) noexcept {}
};

} // namespace chimera::mobile
