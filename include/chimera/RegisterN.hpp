#pragma once
#include <array>
#include <cstdint>
#include <stdexcept>

template <std::size_t Bits>
class RegisterN {
    static_assert(Bits > 0 && Bits % 64 == 0, "Bits must be a positive multiple of 64");
public:
    static constexpr std::size_t WordCount = Bits / 64;
    std::array<std::uint64_t, WordCount> w{};
    RegisterN() = default;
    explicit RegisterN(std::uint64_t x) { w[0] = x; }
    bool is_zero() const { for (auto x : w) if (x) return false; return true; }
    RegisterN operator+(const RegisterN& rhs) const { RegisterN out; unsigned __int128 carry=0; for(std::size_t i=0;i<WordCount;++i){auto s=(unsigned __int128)w[i]+rhs.w[i]+carry;out.w[i]=(std::uint64_t)s;carry=s>>64;} return out; }
    RegisterN operator-(const RegisterN& rhs) const { RegisterN out; std::uint64_t borrow=0; for(std::size_t i=0;i<WordCount;++i){auto a=w[i],b=rhs.w[i];out.w[i]=a-b-borrow;borrow=borrow?(a<=b):(a<b);} return out; }
    RegisterN operator&(const RegisterN& rhs) const { RegisterN out; for(std::size_t i=0;i<WordCount;++i)out.w[i]=w[i]&rhs.w[i];return out; }
    RegisterN operator|(const RegisterN& rhs) const { RegisterN out; for(std::size_t i=0;i<WordCount;++i)out.w[i]=w[i]|rhs.w[i];return out; }
    RegisterN operator^(const RegisterN& rhs) const { RegisterN out; for(std::size_t i=0;i<WordCount;++i)out.w[i]=w[i]^rhs.w[i];return out; }
    RegisterN shl(std::size_t bits) const { RegisterN out; if(bits>=Bits)return out; auto ws=bits/64,bs=bits%64; for(std::size_t i=WordCount;i-->0;){if(i<ws)continue;out.w[i]=w[i-ws]<<bs;if(bs&&i>ws)out.w[i]|=w[i-ws-1]>>(64-bs);}return out; }
    RegisterN shr(std::size_t bits) const { RegisterN out; if(bits>=Bits)return out; auto ws=bits/64,bs=bits%64; for(std::size_t i=0;i<WordCount;++i){if(i+ws>=WordCount)continue;out.w[i]=w[i+ws]>>bs;if(bs&&i+ws+1<WordCount)out.w[i]|=w[i+ws+1]<<(64-bs);}return out; }
    std::uint64_t& operator[](std::size_t i){return w.at(i);} const std::uint64_t& operator[](std::size_t i)const{return w.at(i);}
};
using Reg4096=RegisterN<4096>;
using Reg8192=RegisterN<8192>;
