#pragma once
#include <array>
#include <cmath>
#include <cstddef>
namespace chm::md { template<std::size_t N> struct Vector { std::array<double,N> data{}; double norm()const{double s=0;for(double v:data)s+=v*v;return std::sqrt(s);} double dot(const Vector&o)const{double s=0;for(std::size_t i=0;i<N;++i)s+=data[i]*o.data[i];return s;} }; }
