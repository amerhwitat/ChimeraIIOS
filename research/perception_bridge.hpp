#pragma once
#include <cstddef>
#include <cstdint>
#include <limits>
#include <new>
#include <string>
#include <utility>
#include <vector>

namespace chimera::perception {

enum class Error { ok, invalid_argument, overflow, budget_exceeded, invalid_frame, permission_denied, revoked };

inline bool checked_mul(std::size_t a, std::size_t b, std::size_t& out) noexcept {
    if (a != 0 && b > std::numeric_limits<std::size_t>::max() / a) return false;
    out = a * b;
    return true;
}

struct Budget {
    std::size_t max_dimensions = 8192;
    std::size_t max_vector_bytes = 8u * 1024u * 1024u;
    std::size_t max_frame_bytes = 64u * 1024u * 1024u;
    std::uint32_t max_width = 8192;
    std::uint32_t max_height = 8192;
};

struct FeatureVector {
    std::vector<float> values;
    static Error allocate(std::size_t dimensions, const Budget& budget, FeatureVector& out) noexcept {
        if (dimensions == 0) return Error::invalid_argument;
        if (dimensions > budget.max_dimensions) return Error::budget_exceeded;
        std::size_t bytes = 0;
        if (!checked_mul(dimensions, sizeof(float), bytes)) return Error::overflow;
        if (bytes > budget.max_vector_bytes) return Error::budget_exceeded;
        try { out.values.assign(dimensions, 0.0f); }
        catch (const std::bad_alloc&) { return Error::budget_exceeded; }
        catch (...) { return Error::invalid_argument; }
        return Error::ok;
    }
};

struct FrameView {
    const std::uint8_t* data = nullptr;
    std::size_t payload_bytes = 0;
    std::uint32_t width = 0, height = 0, stride = 0, channels = 0;

    Error validate(const Budget& budget) const noexcept {
        if (!data || width == 0 || height == 0 || channels < 1 || channels > 4) return Error::invalid_frame;
        if (width > budget.max_width || height > budget.max_height) return Error::budget_exceeded;
        std::size_t row_min = 0, total_min = 0;
        if (!checked_mul(static_cast<std::size_t>(width), static_cast<std::size_t>(channels), row_min))
            return Error::overflow;
        if (stride < row_min) return Error::invalid_frame;
        if (!checked_mul(static_cast<std::size_t>(stride), static_cast<std::size_t>(height), total_min))
            return Error::overflow;
        if (total_min > budget.max_frame_bytes) return Error::budget_exceeded;
        if (payload_bytes < total_min) return Error::invalid_frame;
        return Error::ok;
    }
};

enum class Scope : std::uint32_t { capture = 1u, infer = 2u, ocr = 4u };
inline std::uint32_t scope_bit(Scope s) noexcept { return static_cast<std::uint32_t>(s); }

struct Capability {
    std::uint64_t token = 0;
    std::uint64_t session = 0;
    std::uint32_t scopes = 0;
    bool revoked = false;
};

class CapabilityTable {
public:
    Error grant(std::uint64_t token, std::uint64_t session, std::uint32_t scopes) noexcept {
        if (!token || !session || !scopes) return Error::invalid_argument;
        for (auto& c : entries_) if (c.token == token) return Error::invalid_argument;
        try { entries_.push_back({token, session, scopes, false}); }
        catch (...) { return Error::budget_exceeded; }
        return Error::ok;
    }
    Error authorize(std::uint64_t token, std::uint64_t session, Scope scope) const noexcept {
        for (const auto& c : entries_) {
            if (c.token != token) continue;
            if (c.revoked) return Error::revoked;
            if (c.session != session || (c.scopes & scope_bit(scope)) == 0) return Error::permission_denied;
            return Error::ok;
        }
        return Error::permission_denied;
    }
    Error revoke(std::uint64_t token, std::uint64_t session) noexcept {
        for (auto& c : entries_) if (c.token == token) {
            if (c.session != session) return Error::permission_denied;
            c.revoked = true;
            return Error::ok;
        }
        return Error::permission_denied;
    }
private:
    std::vector<Capability> entries_;
};

// The production compositor/model adapters must implement this interface in a
// separately sandboxed worker. This core intentionally never captures a screen,
// downloads models, or claims inference results without an installed backend.
class InferenceBackend {
public:
    virtual ~InferenceBackend() = default;
    virtual bool model_loaded() const noexcept = 0;
    virtual Error infer(const FrameView&, std::vector<std::uint8_t>& typed_result) noexcept = 0;
};

} // namespace chimera::perception
