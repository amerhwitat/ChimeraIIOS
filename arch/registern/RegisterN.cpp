#include "RegisterN.h"
#include <algorithm>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace chimera::arch {
RegisterN::RegisterN(std::size_t bits): bits_(bits), limbs_((bits+63)/64) {
    if (!bits) throw std::invalid_argument("RegisterN width must be positive");
}
RegisterN::RegisterN(std::size_t bits, std::uint64_t fill): RegisterN(bits) {
    std::fill(limbs_.begin(), limbs_.end(), fill); mask_top();
}
void RegisterN::resize(std::size_t bits) {
    if (!bits) throw std::invalid_argument("RegisterN width must be positive");
    bits_=bits; limbs_.resize((bits+63)/64); mask_top();
}
void RegisterN::clear() noexcept { std::fill(limbs_.begin(), limbs_.end(), 0); }
void RegisterN::set_bit(std::size_t i,bool v) { if(i>=bits_) throw std::out_of_range("bit"); auto& x=limbs_[i/64]; const auto m=1ULL<<(i%64); if(v)x|=m;else x&=~m; }
bool RegisterN::get_bit(std::size_t i) const { if(i>=bits_) throw std::out_of_range("bit"); return (limbs_[i/64]>>(i%64))&1ULL; }
void RegisterN::mask_top(){ const auto r=bits_%64; if(r) limbs_.back() &= ((1ULL<<r)-1); }
void RegisterN::require_compatible(const RegisterN& r) const { if(bits_!=r.bits_) throw std::invalid_argument("RegisterN width mismatch"); }
RegisterN& RegisterN::add(const RegisterN& r) {
    require_compatible(r);
    std::uint64_t carry = 0;
    for (std::size_t i = 0; i < limbs_.size(); ++i) {
        const std::uint64_t a = limbs_[i];
        const std::uint64_t b = r.limbs_[i];

        const std::uint64_t sum = a + b;
        const std::uint64_t carry_ab = sum < a ? 1U : 0U;

        const std::uint64_t result = sum + carry;
        const std::uint64_t carry_result = result < sum ? 1U : 0U;

        limbs_[i] = result;
        carry = (carry_ab | carry_result);
    }
    mask_top();
    return *this;
}

RegisterN& RegisterN::sub(const RegisterN& r) {
    require_compatible(r);
    std::uint64_t borrow = 0;
    for (std::size_t i = 0; i < limbs_.size(); ++i) {
        const std::uint64_t a = limbs_[i];
        const std::uint64_t b = r.limbs_[i];

        const std::uint64_t result = a - b - borrow;
        const std::uint64_t borrow_ab = a < b ? 1U : 0U;
        const std::uint64_t borrow_result =
            (borrow != 0 && a == b) ? 1U : 0U;

        limbs_[i] = result;
        borrow = (borrow_ab | borrow_result);
    }
    mask_top();
    return *this;
}
RegisterN& RegisterN::bit_and(const RegisterN&r){require_compatible(r);for(size_t i=0;i<limbs_.size();++i)limbs_[i]&=r.limbs_[i];return *this;}
RegisterN& RegisterN::bit_or(const RegisterN&r){require_compatible(r);for(size_t i=0;i<limbs_.size();++i)limbs_[i]|=r.limbs_[i];mask_top();return *this;}
RegisterN& RegisterN::bit_xor(const RegisterN&r){require_compatible(r);for(size_t i=0;i<limbs_.size();++i)limbs_[i]^=r.limbs_[i];mask_top();return *this;}
RegisterN& RegisterN::shl(size_t n){ if(n>=bits_){clear();return *this;} size_t w=n/64,b=n%64;for(size_t i=limbs_.size();i-->0;){uint64_t v=i>=w?limbs_[i-w]:0;uint64_t carry=(b&&i>w)?limbs_[i-w-1]>>(64-b):0;limbs_[i]=(v<<b)|carry;}mask_top();return *this;}
RegisterN& RegisterN::shr(size_t n){ if(n>=bits_){clear();return *this;} size_t w=n/64,b=n%64;for(size_t i=0;i<limbs_.size();++i){uint64_t v=i+w<limbs_.size()?limbs_[i+w]:0;uint64_t carry=(b&&i+w+1<limbs_.size())?limbs_[i+w+1]<<(64-b):0;limbs_[i]=(v>>b)|carry;}return *this;}
std::string RegisterN::to_hex() const { std::ostringstream o; o<<std::hex<<std::setfill('0'); for(size_t i=limbs_.size();i-->0;) o<<std::setw(16)<<limbs_[i]; return o.str(); }
RegisterN RegisterN::from_hex(size_t bits,const std::string& h){ RegisterN r(bits); std::string s=h; if(s.rfind("0x",0)==0)s=s.substr(2); for(size_t p=0;!s.empty();){size_t take=std::min<size_t>(16,s.size());auto part=s.substr(s.size()-take,take);r.limbs_[p++]=std::stoull(part,nullptr,16);s.resize(s.size()-take);} r.mask_top();return r;}
}
