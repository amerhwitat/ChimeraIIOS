#pragma once
#include <cstddef>
#include <cstdint>
#include <memory>
#include <span>
#include <string>
#include <vector>

namespace chimera::runtime {

// Runtime-selectable width. Width is a data-model property, not a C++ integer type.
struct Width {
    std::size_t bits{64};
    constexpr bool valid() const noexcept { return bits >= 8 && bits % 8 == 0; }
};

enum class ExecutionMode : std::uint8_t {
    Scalar,
    Vector,
    NativeWide,
    JIT,
    QuantumHybrid
};

class WideInt {
public:
    explicit WideInt(Width width = {});
    WideInt(Width width, std::span<const std::uint64_t> limbs);

    Width width() const noexcept { return width_; }
    std::size_t limb_count() const noexcept { return limbs_.size(); }
    std::span<std::uint64_t> limbs() noexcept { return limbs_; }
    std::span<const std::uint64_t> limbs() const noexcept { return limbs_; }

    void clear() noexcept;
    void normalize() noexcept;
    bool is_zero() const noexcept;
    std::string hex() const;

    static WideInt add(const WideInt&, const WideInt&);
    static WideInt sub(const WideInt&, const WideInt&);
    static WideInt bit_and(const WideInt&, const WideInt&);
    static WideInt bit_or(const WideInt&, const WideInt&);
    static WideInt bit_xor(const WideInt&, const WideInt&);
    static WideInt shl(const WideInt&, std::size_t bits);
    static WideInt shr(const WideInt&, std::size_t bits);

private:
    Width width_;
    std::vector<std::uint64_t> limbs_;
};

struct RuntimeCapabilities {
    Width max_width{8192};
    bool vector{true};
    bool jit{false};
    bool quantum_backend{false};
};

class ExecutionBackend {
public:
    virtual ~ExecutionBackend() = default;
    virtual ExecutionMode mode() const noexcept = 0;
    virtual bool supports(Width) const noexcept = 0;
    virtual void barrier() noexcept = 0;
};

class Runtime {
public:
    explicit Runtime(RuntimeCapabilities capabilities = {});

    const RuntimeCapabilities& capabilities() const noexcept { return caps_; }
    ExecutionMode mode() const noexcept { return mode_; }
    Width width() const noexcept { return width_; }

    bool switch_mode(ExecutionMode mode, Width width);
    std::unique_ptr<ExecutionBackend> make_backend() const;

private:
    RuntimeCapabilities caps_;
    ExecutionMode mode_{ExecutionMode::Scalar};
    Width width_{};
};

} // namespace chimera::runtime
