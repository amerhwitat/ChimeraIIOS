#include <cassert>
#include <cmath>
#include "chm/quantum/StateVector.hpp"
int main(){auto s=chm::quantum::bell_state();assert(std::abs(std::norm(s[0])-.5)<1e-12);assert(std::abs(std::norm(s[3])-.5)<1e-12);return 0;}
