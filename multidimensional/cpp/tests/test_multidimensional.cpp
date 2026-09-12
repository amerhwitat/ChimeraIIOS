#include <cassert>
#include <cmath>
#include "chm/md/Vector.hpp"
int main(){chm::md::Vector<128>x{};for(auto&v:x.data)v=1.0;assert(std::abs(x.norm()-std::sqrt(128.0))<1e-12);return 0;}
