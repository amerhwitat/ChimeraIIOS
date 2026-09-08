#pragma once
#include <array>
#include <cstddef>
#include <cmath>

namespace chimera {
struct State128 {
    std::array<double,128> v{};
    double& operator[](std::size_t i) { return v.at(i); }
    const double& operator[](std::size_t i) const { return v.at(i); }
};
inline State128 state_transition(const State128& x, const State128& u) {
    State128 y{}; for(std::size_t i=0;i<128;++i) y[i]=x[i]+u[i]; return y;
}
inline double cosine_similarity(const State128& a,const State128& b){
    double dot=0,aa=0,bb=0;
    for(std::size_t i=0;i<128;++i){dot+=a[i]*b[i];aa+=a[i]*a[i];bb+=b[i]*b[i];}
    return (aa==0||bb==0)?0.0:dot/(std::sqrt(aa)*std::sqrt(bb));
}
}
