#pragma once
#include <complex>
#include <cstddef>
#include <vector>

namespace chm::quantum {
using Complex = std::complex<double>;
using State = std::vector<Complex>;

enum class Gate { X, Y, Z, H, Phase };

State bell_state();
State qft(const State& input);
void apply_single(State& state, std::size_t qubit, Gate gate, double theta = 0.0);
double probability_sum(const State& state);
}
