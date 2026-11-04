#include <cstdint>
#include <vector>
#include <algorithm>
namespace chimera {
struct Task { uint64_t id=0, deadline=0, priority=0, energy=0, memory=0, accelerator=0, dependency=0, confidence=0, importance=0; bool runnable=true; };
inline double scheduling_score(const Task&t,uint64_t now){
    const double deadline = t.deadline>now ? 1.0/double(t.deadline-now) : 1e9;
    return 4*t.priority + 2*t.importance + 2*t.confidence + deadline + 1.0/(1+t.energy+t.memory) + t.accelerator + t.dependency;
}
class Chronos {
    std::vector<Task> q_;
public:
    void submit(Task t){q_.push_back(t);}
    const Task* next(uint64_t now) const { const Task* best=nullptr; double score=-1e300; for(const auto&t:q_) if(t.runnable && scheduling_score(t,now)>score){score=scheduling_score(t,now);best=&t;} return best; }
};
}
