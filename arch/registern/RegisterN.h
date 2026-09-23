#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>
#include <span>

namespace chimera::arch {

class RegisterN {
public:
    explicit RegisterN(std::size_t bits = 8192);
    RegisterN(std::size_t bits, std::uint64_t fill);

    std::size_t bit_width() const noexcept { return bits_; }
    std::size_t limb_count() const noexcept { return limbs_.size(); }
    std::span<std::uint64_t> limbs() noexcept { return limbs_; }
    std::span<const std::uint64_t> limbs() const noexcept { return limbs_; }

    void resize(std::size_t bits);
    void clear() noexcept;
    void set_bit(std::size_t index, bool value);
    bool get_bit(std::size_t index) const;
    std::string to_hex() const;
    static RegisterN from_hex(std::size_t bits, const std::string& hex);

    RegisterN& add(const RegisterN& rhs);
    RegisterN& sub(const RegisterN& rhs);
    RegisterN& bit_and(const RegisterN& rhs);
    RegisterN& bit_or(const RegisterN& rhs);
    RegisterN& bit_xor(const RegisterN& rhs);
    RegisterN& shl(std::size_t count);
    RegisterN& shr(std::size_t count);

private:
    std::size_t bits_;
    std::vector<std::uint64_t> limbs_;
    void mask_top();
    void require_compatible(const RegisterN& rhs) const;
};

} // namespace chimera::arch
