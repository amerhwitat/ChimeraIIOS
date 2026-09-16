#include "chimera/ai/runtime.h"
#include <cassert>
using namespace chimera::ai;
int main(){
 DeviceProfile cpu{DeviceClass::CPU,16384,8,false,false}; DeviceProfile npu{DeviceClass::NPU,8192,16,true,false};
 WorkloadProfile w{}; w.latency_sensitive=true; w.context_tokens=512; auto p=RuntimePlanner::choose(w,{cpu,npu}); assert(p.strategy==Strategy::Speculative); assert(p.device==DeviceClass::NPU); assert(p.parallel_units==16); assert(p.offload);
 WorkloadProfile m{}; m.memory_constrained=true; m.model_parameters=2000000000ULL; p=RuntimePlanner::choose(m,{cpu}); assert(p.strategy==Strategy::Quantized);
 return 0;
}
