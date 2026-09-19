#include "chimera/ai/runtime.h"
#include <algorithm>
namespace chimera::ai {
InferencePlan RuntimePlanner::choose(const WorkloadProfile& w, const std::vector<DeviceProfile>& devices) {
    InferencePlan p;
    auto best = std::max_element(devices.begin(), devices.end(), [](const auto& a, const auto& b){ return (a.accelerator ? 2u : 0u) + a.compute_units < (b.accelerator ? 2u : 0u) + b.compute_units; });
    if (best != devices.end()) { p.device = best->device; p.parallel_units = std::max(1u, best->compute_units); }
    if (w.mixture_of_experts) p.strategy = Strategy::MixtureOfExperts;
    else if (w.distributed) { p.strategy = Strategy::Distributed; p.network_required = true; }
    else if (w.memory_constrained && w.model_parameters > 1000000000ULL) p.strategy = Strategy::Quantized;
    else if (w.latency_sensitive && w.context_tokens > 128) p.strategy = Strategy::Speculative;
    else if (w.streaming) p.strategy = Strategy::Streaming;
    else if (w.batch_size > 1) p.strategy = Strategy::Batched;
    p.offload = best != devices.end() && best->accelerator && best->device != DeviceClass::CPU;
    return p;
}
const char* RuntimePlanner::strategy_name(Strategy s) noexcept { switch(s){case Strategy::Eager:return "eager";case Strategy::Batched:return "batched";case Strategy::Streaming:return "streaming";case Strategy::Speculative:return "speculative";case Strategy::MixtureOfExperts:return "mixture_of_experts";case Strategy::KVCacheOptimized:return "kv_cache_optimized";case Strategy::Quantized:return "quantized";case Strategy::Sparse:return "sparse";case Strategy::SplitInference:return "split_inference";case Strategy::Distributed:return "distributed";} return "unknown"; }
const char* RuntimePlanner::device_name(DeviceClass d) noexcept { switch(d){case DeviceClass::CPU:return "cpu";case DeviceClass::SIMD:return "simd";case DeviceClass::GPU:return "gpu";case DeviceClass::NPU:return "npu";case DeviceClass::FPGA:return "fpga";case DeviceClass::DSP:return "dsp";case DeviceClass::Edge:return "edge";case DeviceClass::IoT:return "iot";} return "unknown"; }
} // namespace chimera::ai
