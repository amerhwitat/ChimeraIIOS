#pragma once
#include <array>
#include <cstdint>
#include <cstddef>
#include <string>
#include <stdexcept>
#include <algorithm>
#include <sstream>
#include <iomanip>

namespace chimera {

template <std::size_t Bits>
class RegisterN {
    static_assert(Bits > 0 && Bits % 64 == 0, "RegisterN width must be a positive multiple of 64");
public:
    static constexpr std::size_t kBits = Bits;
    static constexpr std::size_t kLanes = Bits / 64;
    using storage_type = std::array<std::uint64_t, kLanes>;

    constexpr RegisterN() noexcept = default;
    explicit constexpr RegisterN(std::uint64_t v) noexcept { set_u64(0, v); }

    constexpr std::uint64_t lane(std::size_t i) const noexcept { return words_[i]; }
    constexpr void set_u64(std::size_t i, std::uint64_t v) noexcept { words_[i] = v; }
    constexpr const storage_type& words() const noexcept { return words_; }

    std::string toHex() const {
        std::ostringstream os;
        os << std::hex << std::setfill('0');
        for (std::size_t i = kLanes; i-- > 0;) os << std::setw(16) << words_[i];
        return os.str();
    }

    static RegisterN fromHex(std::string hex) {
        const std::size_t expected = Bits / 4;
        if (hex.size() > expected) throw std::invalid_argument("RegisterN hex value is too wide");
        hex.insert(hex.begin(), expected - hex.size(), '0');
        RegisterN r;
        for (std::size_t lane = 0; lane < kLanes; ++lane) {
            const std::size_t end = expected - lane * 16;
            const std::size_t begin = end - 16;
            r.words_[lane] = std::stoull(hex.substr(begin, 16), nullptr, 16);
        }
        return r;
    }

    friend constexpr RegisterN operator+(const RegisterN& a, const RegisterN& b) noexcept {
        RegisterN r; unsigned __int128 carry = 0;
        for (std::size_t i = 0; i < kLanes; ++i) {
            const unsigned __int128 sum = (unsigned __int128)a.words_[i] + b.words_[i] + carry;
            r.words_[i] = (std::uint64_t)sum; carry = sum >> 64;
        }
        return r;
    }
    friend constexpr RegisterN operator-(const RegisterN& a, const RegisterN& b) noexcept {
        RegisterN r; std::uint64_t borrow = 0;
        for (std::size_t i = 0; i < kLanes; ++i) {
            const std::uint64_t bi = b.words_[i] + borrow;
            const std::uint64_t next = (bi < b.words_[i]) ? 1 : 0;
            r.words_[i] = a.words_[i] - bi;
            borrow = next | (a.words_[i] < bi ? 1 : 0);
        }
        return r;
    }
    friend constexpr RegisterN operator&(const RegisterN& a, const RegisterN& b) noexcept { return bitop(a,b,[](auto x,auto y){return x&y;}); }
    friend constexpr RegisterN operator|(const RegisterN& a, const RegisterN& b) noexcept { return bitop(a,b,[](auto x,auto y){return x|y;}); }
    friend constexpr RegisterN operator^(const RegisterN& a, const RegisterN& b) noexcept { return bitop(a,b,[](auto x,auto y){return x^y;}); }

private:
    storage_type words_{};
    template<class F> static constexpr RegisterN bitop(const RegisterN&a,const RegisterN&b,F f) noexcept {
        RegisterN r; for(std::size_t i=0;i<kLanes;++i) r.words_[i]=f(a.words_[i],b.words_[i]); return r;
    }
};

using Register8192 = RegisterN<8192>;
using Register4096 = RegisterN<4096>;

} // namespace chimera
