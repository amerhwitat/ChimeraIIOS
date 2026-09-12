#include "chm/quantum/StateVector.hpp"
#include <cmath>
namespace chm::quantum { State bell_state(){double s=1/std::sqrt(2.0);return {{s,0},{0,0},{0,0},{s,0}};} State qft(const State& in){double pi=std::acos(-1.0);size_t n=in.size();State out(n);for(size_t k=0;k<n;k++){for(size_t x=0;x<n;x++)out[k]+=in[x]*std::exp(Complex{0,2*pi*k*x/(double)n});out[k]/=std::sqrt((double)n);}return out;} }
