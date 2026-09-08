#pragma once
#include "chimera/isa_catalog.hpp"
#include "chimera/nbit_runtime.hpp"
#include <optional>
#include <string_view>

namespace chimera::isa {
struct RuntimeProfile {
    Family family{Family::Chimera};
    runtime::Width width{8192};
    runtime::ExecutionMode mode{runtime::ExecutionMode::Scalar};
};

inline std::optional<RuntimeProfile> profile_for(std::string_view name, std::size_t requested_bits = 0) noexcept {
    const auto* isa = find(name);
    if (!isa) return std::nullopt;
    const std::size_t bits = requested_bits ? requested_bits : isa->natural_width_bits;
    if (bits < 8 || bits % 8 != 0) return std::nullopt;
    return RuntimeProfile{isa->family, runtime::Width{bits}, runtime::ExecutionMode::Scalar};
}
} // namespace chimera::isa
