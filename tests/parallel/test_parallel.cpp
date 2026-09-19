#include "chimera/parallel/parallel.h"
#include <cassert>
#include <numeric>
#include <vector>
using namespace chimera::parallel;
int main(){ std::vector<int> v(100,0); Executor one(1); one.parallel_for(0,v.size(),[&](std::size_t i){v[i]=1;}); assert(std::accumulate(v.begin(),v.end(),0)==100); Executor many(4); many.parallel_for(0,v.size(),[&](std::size_t i){v[i]+=1;}); assert(std::accumulate(v.begin(),v.end(),0)==200); return 0; }
