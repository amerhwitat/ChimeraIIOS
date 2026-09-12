#include "chm/quantum/StateVector.hpp"
#include <cmath>
#include <stdexcept>

namespace chm::quantum {
State bell_state() {
    const double s = 1.0 / std::sqrt(2.0);
    return {{s,0},{0,0},{0,0},{s,0}};
}

State qft(const State& in) {
    const double pi = std::acos(-1.0);
    const std::size_t n = in.size();
    if (n == 0) return {};
    State out(n, Complex{0,0});
    for (std::size_t k=0; k<n; ++k)
        for (std::size_t x=0; x<n; ++x)
            out[k] += in[x] * std::exp(Complex{0, -2*pi*static_cast<double>(k*x)/static_cast<double>(n)});
    const double scale = 1.0 / std::sqrt(static_cast<double>(n));
    for (auto& a : out) a *= scale;
    return out;
}

void apply_single(State& state, std::size_t qubit, Gate gate, double theta) {
    if (state.empty() || (state.size() & (state.size()-1)) != 0) throw std::invalid_argument("state dimension must be a power of two");
    const std::size_t bit = std::size_t{1} << qubit;
    if (bit >= state.size()) throw std::out_of_range("qubit index");
    const double s = 1.0/std::sqrt(2.0);
    Complex a{1,0}, b{0,0}, c{0,0}, d{1,0};
    switch (gate) {
        case Gate::X: a={0,0}; b={1,0}; c={1,0}; d={0,0}; break;
        case Gate::Y: a={0,0}; b={0,-1}; c={0,1}; d={0,0}; break;
        case Gate::Z: d={-1,0}; break;
        case Gate::H: a={s,0}; b={s,0}; c={s,0}; d={-s,0}; break;
        case Gate::Phase: d=std::exp(Complex{0,theta}); break;
    }
    for (std::size_t i=0; i<state.size(); ++i) {
        if (i & bit) continue;
        const std::size_t j=i|bit; const Complex x=state[i], y=state[j];
        state[i]=a*x+b*y; state[j]=c*x+d*y;
    }
}

double probability_sum(const State& state) {
    double sum=0; for (const auto& a: state) sum += std::norm(a); return sum;
}
}
