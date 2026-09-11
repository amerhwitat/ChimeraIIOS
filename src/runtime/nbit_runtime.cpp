#include "chimera/nbit_runtime.hpp"
#include <algorithm>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace chimera::runtime {
namespace {
class BasicBackend final : public ExecutionBackend {
public:
    BasicBackend(ExecutionMode mode, Width width) : mode_(mode), width_(width) {}
    ExecutionMode mode() const noexcept override { return mode_; }
    bool supports(Width width) const noexcept { return width.valid() && width.bits <= width_.bits; }
    void barrier() noexcept override {}
private:
    ExecutionMode mode_;
    Width width_;
};

static void require_compatible(const WideInt& a, const WideInt& b) {
    if (a.width().bits != b.width().bits) throw std::invalid_argument("Chimera N-bit operands have different widths");
}
}

WideInt::WideInt(Width width) : width_(width), limbs_((width.bits + 63) / 64, 0) {
    if (!width.valid()) throw std::invalid_argument("invalid N-bit width");
}

WideInt::WideInt(Width width, std::span<const std::uint64_t> limbs) : WideInt(width) {
    std::copy_n(limbs.begin(), std::min(limbs.size(), limbs_.size()), limbs_.begin());
    normalize();
}

void WideInt::clear() noexcept { std::fill(limbs_.begin(), limbs_.end(), 0); }
bool WideInt::is_zero() const noexcept { return std::all_of(limbs_.begin(), limbs_.end(), [](auto x){ return x == 0; }); }

void WideInt::normalize() noexcept {
    const std::size_t rem = width_.bits % 64;
    if (rem) limbs_.back() &= ((std::uint64_t{1} << rem) - 1);
}

std::string WideInt::hex() const {
    std::ostringstream out;
    out << "0x" << std::hex << std::setfill('0');
    for (auto it = limbs_.rbegin(); it != limbs_.rend(); ++it) out << std::setw(16) << *it;
    return out.str();
}

WideInt WideInt::add(const WideInt& a, const WideInt& b) {
    require_compatible(a, b);
    WideInt result(a.width());
    std::uint64_t carry = 0;
    for (std::size_t i = 0; i < result.limb_count(); ++i) {
        const auto x = a.limbs()[i], y = b.limbs()[i];
        const auto xy = x + y;
        const auto c1 = xy < x;
        const auto sum = xy + carry;
        const auto c2 = sum < xy;
        result.limbs()[i] = sum;
        carry = static_cast<std::uint64_t>(c1 || c2);
    }
    result.normalize();
    return result;
}

WideInt WideInt::sub(const WideInt& a, const WideInt& b) {
    require_compatible(a, b);
    WideInt result(a.width());
    std::uint64_t borrow = 0;
    for (std::size_t i = 0; i < result.limb_count(); ++i) {
        const auto x = a.limbs()[i], y = b.limbs()[i];
        const auto xy = x - y;
        const auto b1 = x < y;
        const auto diff = xy - borrow;
        const auto b2 = xy < borrow;
        result.limbs()[i] = diff;
        borrow = static_cast<std::uint64_t>(b1 || b2);
    }
    result.normalize();
    return result;
}

WideInt WideInt::bit_and(const WideInt& a, const WideInt& b) {
    require_compatible(a, b);
    WideInt result(a.width());
    for (std::size_t i = 0; i < result.limb_count(); ++i) result.limbs()[i] = a.limbs()[i] & b.limbs()[i];
    return result;
}

WideInt WideInt::bit_or(const WideInt& a, const WideInt& b) {
    require_compatible(a, b);
    WideInt result(a.width());
    for (std::size_t i = 0; i < result.limb_count(); ++i) result.limbs()[i] = a.limbs()[i] | b.limbs()[i];
    result.normalize();
    return result;
}

WideInt WideInt::bit_xor(const WideInt& a, const WideInt& b) {
    require_compatible(a, b);
    WideInt result(a.width());
    for (std::size_t i = 0; i < result.limb_count(); ++i) result.limbs()[i] = a.limbs()[i] ^ b.limbs()[i];
    return result;
}

WideInt WideInt::shl(const WideInt& a, std::size_t bits) {
    WideInt result(a.width());
    if (bits >= a.width().bits) return result;
    const std::size_t word_shift = bits / 64;
    const std::size_t bit_shift = bits % 64;
    for (std::size_t dst = a.limb_count(); dst-- > 0;) {
        if (dst < word_shift) continue;
        const std::size_t src = dst - word_shift;
        result.limbs()[dst] |= a.limbs()[src] << bit_shift;
        if (bit_shift != 0 && src > 0) result.limbs()[dst] |= a.limbs()[src - 1] >> (64 - bit_shift);
    }
    result.normalize();
    return result;
}

WideInt WideInt::shr(const WideInt& a, std::size_t bits) {
    WideInt result(a.width());
    if (bits >= a.width().bits) return result;
    const std::size_t word_shift = bits / 64;
    const std::size_t bit_shift = bits % 64;
    for (std::size_t dst = 0; dst < a.limb_count(); ++dst) {
        const std::size_t src = dst + word_shift;
        if (src >= a.limb_count()) break;
        result.limbs()[dst] |= a.limbs()[src] >> bit_shift;
        if (bit_shift != 0 && src + 1 < a.limb_count()) result.limbs()[dst] |= a.limbs()[src + 1] << (64 - bit_shift);
    }
    result.normalize();
    return result;
}

Runtime::Runtime(RuntimeCapabilities capabilities) : caps_(capabilities) {
    if (!caps_.max_width.valid()) throw std::invalid_argument("invalid runtime maximum width");
}

bool Runtime::switch_mode(ExecutionMode mode, Width width) {
    if (!width.valid() || width.bits > caps_.max_width.bits) return false;
    if (mode == ExecutionMode::Vector && !caps_.vector) return false;
    if (mode == ExecutionMode::JIT && !caps_.jit) return false;
    if (mode == ExecutionMode::QuantumHybrid && !caps_.quantum_backend) return false;
    width_ = width;
    mode_ = mode;
    return true;
}

std::unique_ptr<ExecutionBackend> Runtime::make_backend() const {
    return std::make_unique<BasicBackend>(mode_, width_);
}

} // namespace chimera::runtime
