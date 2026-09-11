#pragma once
#include <cstdint>

namespace chimera::nucleus {

enum class ValueType : std::uint8_t { Integer, Float, Text, Vector, Tensor, Blob };

struct RecordHeader {
    std::uint64_t id{};
    std::uint64_t timestamp_ns{};
    ValueType type{ValueType::Blob};
    std::uint32_t size{};
    std::uint32_t flags{};
};

struct QueryBudget {
    std::uint32_t max_rows{1024};
    std::uint32_t max_us{1000};
    bool allow_accelerator{true};
};

} // namespace chimera::nucleus
