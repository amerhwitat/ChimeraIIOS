#pragma once
// Chimera II N-bit integer runtime.
// Logical width is independent of the physical host ISA. Storage is little-endian
// 64-bit limbs; the final limb is masked to the requested width.
#include <algorithm>
#include <cstdint>
#include <initializer_list>
#include <stdexcept>
#include <vector>

namespace chimera::nbit {
class uintN {
    std::size_t bits_{};
    std::vector<std::uint64_t> limbs_;
    void mask_top() {
        if (!bits_ || limbs_.empty()) return;
        const unsigned rem = static_cast<unsigned>(bits_ & 63u);
        if (rem) limbs_.back() &= ((std::uint64_t{1} << rem) - 1u);
    }
public:
    explicit uintN(std::size_t bits, std::uint64_t value = 0) : bits_(bits), limbs_((bits + 63) / 64, 0) {
        if (bits == 0) throw std::invalid_argument("N-bit width must be greater than zero");
        limbs_[0] = value; mask_top();
    }
    std::size_t bits() const noexcept { return bits_; }
    const std::vector<std::uint64_t>& limbs() const noexcept { return limbs_; }
    uintN& operator+=(const uintN& rhs) {
        if (bits_ != rhs.bits_) throw std::invalid_argument("N-bit widths differ");
        std::uint64_t carry = 0;
        for (std::size_t i = 0; i < limbs_.size(); ++i) {
            const std::uint64_t old = limbs_[i];
            const std::uint64_t a = old + rhs.limbs_[i];
            const std::uint64_t c1 = (a < old);
            const std::uint64_t b = a + carry;
            const std::uint64_t c2 = (b < a);
            limbs_[i] = b; carry = c1 | c2;
        }
        mask_top(); return *this;
    }
    friend uintN operator+(uintN lhs, const uintN& rhs) { return lhs += rhs; }
    uintN& operator-=(const uintN& rhs) {
        if (bits_ != rhs.bits_) throw std::invalid_argument("N-bit widths differ");
        std::uint64_t borrow = 0;
        for (std::size_t i = 0; i < limbs_.size(); ++i) {
            const std::uint64_t a = limbs_[i], b = rhs.limbs_[i];
            const std::uint64_t t = a - b;
            const std::uint64_t b1 = (a < b);
            const std::uint64_t r = t - borrow;
            const std::uint64_t b2 = (t < borrow);
            limbs_[i] = r; borrow = b1 | b2;
        }
        mask_top(); return *this;
    }
    friend uintN operator-(uintN lhs, const uintN& rhs) { return lhs -= rhs; }
    uintN& operator<<=(std::size_t shift) {
        if (shift >= bits_) { std::fill(limbs_.begin(), limbs_.end(), 0); return *this; }
        const std::size_t words = shift / 64, rem = shift % 64;
        if (words) for (std::size_t i = limbs_.size(); i-- > words;) limbs_[i] = limbs_[i - words];
        if (words) std::fill(limbs_.begin(), limbs_.begin() + words, 0);
        if (rem) for (std::size_t i = limbs_.size(); i-- > 0;) {
            const std::uint64_t hi = limbs_[i] << rem;
            const std::uint64_t lo = (i ? limbs_[i-1] >> (64-rem) : 0);
            limbs_[i] = hi | lo;
        }
        mask_top(); return *this;
    }
    friend uintN operator<<(uintN v, std::size_t s) { return v <<= s; }
};
}
