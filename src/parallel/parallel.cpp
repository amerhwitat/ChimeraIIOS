#include "chimera/parallel/parallel.h"
#include <algorithm>
#include <thread>
#include <vector>
namespace chimera::parallel {
Executor::Executor(unsigned workers): workers_(std::max(1u,workers)) {}
unsigned Executor::workers() const noexcept { return workers_; }
void Executor::parallel_for(std::size_t begin,std::size_t end,const std::function<void(std::size_t)>& fn) const {
 if(end<=begin) return; const auto count=end-begin; const auto n=std::min<std::size_t>(workers_,count); std::vector<std::thread> ts; ts.reserve(n);
 for(std::size_t t=0;t<n;++t) ts.emplace_back([=,&fn]{ const auto first=begin+(count*t)/n; const auto last=begin+(count*(t+1))/n; for(auto i=first;i<last;++i) fn(i); });
 for(auto& t:ts) t.join();
}
} // namespace chimera::parallel
