#pragma once
#include <cstddef>
#include <vector>
namespace chimera::ai {
enum class DeviceClass { CPU, SIMD, GPU, NPU, FPGA, DSP, Edge, IoT };
enum class Strategy { Eager, Batched, Streaming, Speculative, MixtureOfExperts, KVCacheOptimized, Quantized, Sparse, SplitInference, Distributed };
struct DeviceProfile { DeviceClass device{DeviceClass::CPU}; std::size_t memory_mb{0}; unsigned compute_units{1}; bool accelerator{false}; bool networked{false}; };
struct WorkloadProfile { std::size_t model_parameters{0}; std::size_t context_tokens{0}; std::size_t batch_size{1}; bool streaming{false}; bool mixture_of_experts{false}; bool latency_sensitive{false}; bool memory_constrained{false}; bool distributed{false}; };
struct InferencePlan { Strategy strategy{Strategy::Eager}; DeviceClass device{DeviceClass::CPU}; unsigned parallel_units{1}; bool offload{false}; bool network_required{false}; };
class RuntimePlanner { public: static InferencePlan choose(const WorkloadProfile&, const std::vector<DeviceProfile>&); static const char* strategy_name(Strategy) noexcept; static const char* device_name(DeviceClass) noexcept; };
} // namespace chimera::ai
