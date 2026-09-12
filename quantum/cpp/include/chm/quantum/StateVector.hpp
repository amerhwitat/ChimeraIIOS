#pragma once
#include <complex>
#include <vector>
namespace chm::quantum { using Complex=std::complex<double>; using State=std::vector<Complex>; State bell_state(); State qft(const State& input); }
